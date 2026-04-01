from io import BufferedReader
from os.path import getsize
import warnings

import numpy as np

from ..entries.tag_entry import TagEntry
from ..helper_functions.group_structs import ChannelGroup, LedGroup
from ..helper_functions.parse_guid import parse_guid
from ..helper_functions.read_string import read_string
from ..helper_functions.date_time import DateTime
from ..plate_management.channel_mapping import ChannelMapping
from ..plate_management.led_position import LedPosition
from .tag_type import TagType
from .stimulation.event_data import StimulationEventData
from ..entries.channel_array import BasicChannelArray

class Tag:
    def __init__(self, guid):
        self.tag_guid = guid
        self.head_revision_number = -1
        self.entry_nodes:list[TagEntry] = []
        self.type:TagType = None

    def promote(self, file_id):
        entry_nodes_sorted = sorted(self.entry_nodes, key=lambda entry: entry.revision_number)
        head = entry_nodes_sorted[-1] if entry_nodes_sorted else None

        try:
            if head.type.value == TagType.USER_ANNOTATION or head.type == TagType.SYSTEM_ANNOTATION:
                new = Annotation(file_id, head)
            elif head.type.value == TagType.WELL_TREATMENT:
                new = WellInformation(file_id, head)
            elif head.type.value == TagType.STIMULATION_EVENT:
                new = StimulationEvent(file_id, head)
            elif head.type.value == TagType.STIMULATION_CHANNEL_GROUP:
                new = StimulationChannels(file_id, head)
            elif head.type.value == TagType.STIMULATION_WAVEFORM:
                new = StimulationWaveform(file_id, head)
            elif head.type.value == TagType.CALIBRATION_TAG:
                new = Tag(self.tag_guid)
            elif head.type.value == TagType.STIMULATION_LED_GROUP:
                new = StimulationLeds(file_id, head)
            elif head.type.value == TagType.DOSE_EVENT:
                new = Tag(self.tag_guid)
            elif head.type.value == TagType.STRING_DICTIONARY_KEY_PAIR:
                new = KeyValuePairTag(file_id, head)
            elif head.type.value == TagType.VIABILITY_IMPEDANCE_EVENT:
                new = ViabilityImpedanceTag(file_id, head)
            elif head.type.value == TagType.LEAP_INDUCTION_EVENT:
                new = LeapInductionEvent(file_id, head)
            else:
                new = Tag(self.tag_guid)
                if self.type.value != TagType.DELETED:
                    warnings.warn("Unknown Tag Type found. Is this loader out of date?")
            new.type = head.type
        except ValueError as error:
            if head is None:
                error = ValueError("No tags in list")
            warnings.warn(f"Could not load tag - {error}")
            new = Tag(self.tag_guid)
            new.type = TagType.DELETED

        new.entry_nodes = entry_nodes_sorted
        new.head_revision_number = head.revision_number if head else -1
        return new

    def add_node(self, node):
        self.entry_nodes.append(node)
        self.entry_nodes.sort(key=lambda entry: entry.revision_number)
        self.head_revision_number = max(entry.revision_number for entry in self.entry_nodes)
        self.type = self.entry_nodes[-1].type

class EventTag(Tag):
    """
    EventTag base class for tagged events in the file. Indicates
    time stamps for particular events"""

    def __init__(self, file_id:BufferedReader, raw_tag:TagEntry):
        super().__init__(raw_tag.tag_guid)

        start = raw_tag.start + TagEntry.BASE_SIZE
        file_id.seek(start)

        if start < getsize(file_id.name):
            self.sampling_frequency:np.double = np.fromfile(file_id, np.double, 1)[0]
            self.event_time_sample:np.int64 = np.fromfile(file_id, np.int64, 1)[0]
            self.event_duration_samples:np.int64 = np.fromfile(file_id, np.int64, 1)[0]
            self.event_time = np.double(self.event_time_sample / self.sampling_frequency)
        else:
            raise ValueError(f'Encountered an error while loading EventTag {raw_tag.tag_guid}')

class Annotation(EventTag):
    """Annotation tag that corresponds to events listed in AxIS's play bar"""

    def __init__(self, file_id:BufferedReader, raw_tag:TagEntry):
        super().__init__(file_id, raw_tag)

        # Assume EventTag constructor leaves us at the right place 
        self.well_column = int.from_bytes(file_id.read(1), 'little', signed=False)
        self.well_row = int.from_bytes(file_id.read(1), 'little', signed=False)
        self.electrode_column = int.from_bytes(file_id.read(1), 'little', signed=False)
        self.electrode_row = int.from_bytes(file_id.read(1), 'little', signed=False)

        # Annotations are always broadcast
        if (self.well_column != 0 or self.well_row != 0 or
            self.electrode_column != 0 or self.electrode_row != 0):
            print('File may be corrupted')

        self.note_text = read_string(file_id)

        start = raw_tag.start + TagEntry.BASE_SIZE
        if file_id.tell() > (start + raw_tag.entry_record.length):
            print('File may be corrupted')

class LeapInductionEvent(Tag):
    """
    LEAPINDUCTIONEVENT Tag that describes a LEAP induction event
    """

    current_version = 0

    def __init__(self, file_id:BufferedReader, raw_tag:TagEntry):
        super().__init__(raw_tag.tag_guid)

        start = raw_tag.start + TagEntry.BASE_SIZE

        # matlabs fseek checks boundaries of the file and returns
        # an error if fseek exceeds the file boundaries
        # however, python does not check this and thus the file size has
        # to be used as a reference
        file_id.seek(start)
        self.creation_date = raw_tag.creation_date
        if start < getsize(file_id.name):

            version = np.fromfile(file_id, dtype=np.uint16, count=2)
            version = version[0]  # Second short is ignored

            if version != LeapInductionEvent.current_version:
                raise ValueError('Unknown LEAP induction event version')

            self.leap_induction_start_time = DateTime(file_id)

            ticks = np.fromfile(file_id, dtype=np.uint64, count=1)[0]
            self.leap_induction_duration = np.double(ticks) * 1e-7

            self.plate_type:np.uint32 = np.fromfile(file_id, dtype=np.uint32, count=1)[0]
            num_channels = np.fromfile(file_id, dtype=np.uint32, count=1)[0]

            self.leaped_channels = [ChannelMapping.from_file(file_id) for _ in range(num_channels)]

        else:
            raise ValueError('Encountered an error while loading '
                             f'LeapInductionEvent {raw_tag.tag_guid}')

        start = raw_tag.start + TagEntry.BASE_SIZE
        if file_id.tell() > (start + raw_tag.entry_record.length):
            print('File may be corrupted')

class WellInformation(Tag):
    """WellInformation: Class that describes the platemap data for a single well"""
    def __init__(self, file_id:BufferedReader, raw_tag:TagEntry):
        super().__init__(raw_tag.tag_guid)

        start = raw_tag.start + TagEntry.BASE_SIZE
        end = raw_tag.start + raw_tag.entry_record.length
        file_id.seek(start)

        if start < getsize(file_id.name):
            self.well_column:np.uint8 = np.fromfile(file_id, np.uint8, 1)[0]
            self.well_row:np.uint8 = np.fromfile(file_id, np.uint8, 1)[0]
            electrode_column:np.uint8 = np.fromfile(file_id, np.uint8, 1)[0]
            electrode_row:np.uint8 = np.fromfile(file_id, np.uint8, 1)[0]

            # Verify well coordinates
            if self.well_column == 0 or self.well_row == 0:
                raise ValueError(f'WellInformationTag {raw_tag.tag_guid} contains invalid data')

            # Electrode position should always be broadcast to well here
            if electrode_column != 0 or electrode_row != 0:
                print('File may be corrupted')

            well_type:np.uint8 = np.fromfile(file_id, np.uint8, 1)[0]
            self.is_on = bool(well_type & 1)
            self.is_control = bool(well_type & 2)

            bytes_remaining = end - file_id.tell()

            # We should have at least 12 bytes remaining: 3 for RGB, at least 8 for empty strings,
            # and 1 for TreatmentHowMuchUnitExponent
            if bytes_remaining >= 12:
                self.red:np.uint8 = np.fromfile(file_id, np.uint8, 1)[0]
                self.green:np.uint8 = np.fromfile(file_id, np.uint8, 1)[0]
                self.blue:np.uint8 = np.fromfile(file_id, np.uint8, 1)[0]

                # User Treatment Data
                self.treatment_what = read_string(file_id)
                self.additional_information = read_string(file_id)

                bytes_remaining = end - file_id.tell()

                # Make sure we have at least 13 bytes remaining - 8 for TreatmentHowMuchBaseValue,
                # 1 for exponent, 4 for empty string
                if bytes_remaining > 9:
                    self.treatment_how_much_base_value:np.double =\
                        np.fromfile(file_id, np.double, 1)[0]
                    self.treatment_how_much_unit_exponent:np.int8 =\
                        np.fromfile(file_id, np.int8, 1)[0]
                    self.treatment_how_much_base_unit = read_string(file_id)
                else:
                    self.treatment_how_much_base_value = np.double(0.0)
                    self.treatment_how_much_unit_exponent = np.int8(0)
                    self.treatment_how_much_base_unit = ''
                    print(f'Tag {raw_tag.tag_guid} is missing treatment amount')
            else:
                self.red = np.uint8(255)
                self.green = np.uint8(255)
                self.blue = np.uint8(255)
                self.treatment_what = ''
                self.additional_information = ''
                self.treatment_how_much_base_value = np.double(0.0)
                self.treatment_how_much_unit_exponent = np.int8(0)
                print(f'Tag {raw_tag.tag_guid} is an old-style tag - no treatment data')

            if file_id.tell() > end:
                print('File may be corrupted')
        else:
            raise ValueError('Encountered an error while loading '
                             f'WellInformation {raw_tag.tag_guid}')

class StimulationChannels(Tag):
    """
    StimulationChannels: File data that enumerates channels used in a stimulation
    """
    current_version = 0
    min_array_size = np.int64(20)

    def __init__(self, file_id:BufferedReader, raw_tag:TagEntry):
        super().__init__(raw_tag.tag_guid)

        # Move to the correct location in the file
        start = np.int64(raw_tag.start + TagEntry.BASE_SIZE)

        tag_start = np.int64(raw_tag.start)
        tag_end = np.int64(tag_start + raw_tag.entry_record.length)
        file_id.seek(start)

        if start < getsize(file_id.name):
            version = np.fromfile(file_id, dtype=np.uint16, count=1)[0]
            if version == StimulationChannels.current_version:
                np.fromfile(file_id, dtype=np.uint16, count=1)  # Reserved short
                self.channel_groups = []

                array = 1
                pos = np.int64(file_id.tell())

                while (tag_end - pos) >= StimulationChannels.min_array_size:
                    id_:np.uint32 = np.fromfile(file_id, dtype=np.uint32, count=1)[0]
                    plate_type:np.uint32 = np.fromfile(file_id, dtype=np.uint32, count=1)[0]

                    num_channels:np.uint32 = np.fromfile(file_id, dtype=np.uint32, count=1)[0]
                    channels = [ChannelMapping.from_file(file_id) for _ in range(num_channels)]

                    self.channel_groups.append(ChannelGroup(id_, plate_type, channels))

                    array += 1
                    pos = np.int64(file_id.tell())
            else:
                self.channel_groups:list[ChannelGroup] = []
                print('Stimulation channels version not supported')
        else:
            raise ValueError('Encountered an error while loading '
                             f'StimulationChannels {raw_tag.tag_guid}')

        if file_id.tell() > (tag_start + raw_tag.entry_record.length):
            print('File may be corrupted')

class StimulationEvent(EventTag):
    # STIMULATIONEVENT Event data that corresponds to a tagged stimulation
    # that occurred in the file

    current_version = 0
    def __init__(self, fileID:BufferedReader, rawTag:TagEntry):
        super().__init__(fileID, rawTag)
        # Assume EventTag leaves us at the correct location in the file
        version = np.fromfile(fileID, np.uint16, 1)[0]
        self.electrodes:list[ChannelGroup] = []
        self.leds:list[LedGroup] = []
        self.plate_type:list[np.uint32] = []
        if version == StimulationEvent.current_version:
            # reserved bytes skipped
            _ = np.fromfile(fileID, np.uint16, 1)[0]
            self.waveform_tag = parse_guid(np.fromfile(fileID, np.uint8, 16))
            self.channels_tag = parse_guid(np.fromfile(fileID, np.uint8, 16))

            self.event_data = np.fromfile(fileID, np.uint16, 1)[0]
            self.sequence_number = np.fromfile(fileID, np.uint16, 1)[0]
        else:
            self.waveform_tag = ''
            self.channels_tag = ''
            self.event_data = np.uint16('FFFF')
            self.sequence_number = np.uint16('FFFF')
            print('Stimulation Event version not supported')

        start = rawTag.start + TagEntry.BASE_SIZE
        if fileID.tell() > (start + rawTag.entry_record.length):
            print('File may be corrupted')

    def link(self, tag_map:dict[str, Tag]):
        if not isinstance(tag_map, dict):
            raise ValueError('Link should be called with a dict')

        if self.waveform_tag in tag_map.keys():
            self.waveform_tag = tag_map[self.waveform_tag]
        else:
            print(f'Missing Stimulation Waveform Tag: {self.waveform_tag}')

        if self.channels_tag in tag_map.keys():
            self.channels_tag = tag_map[self.channels_tag]
        else:
            print(f'Missing Stimulation Channels Tag: {self.channels_tag}')

        if isinstance(self.waveform_tag, StimulationWaveform)\
            and isinstance(self.channels_tag, StimulationChannels):
            event_data = self.waveform_tag.tag_blocks
            channels = self.channels_tag.channel_groups
            # the next() command returns the first item in the list
            # and is thus equivalent to a matlab construct like
            # arrayA(find(arrayB,1)) where arrayB contains truth values
            self.event_data = next((e for e in event_data if e.id == self.event_data), None)

            self.electrodes = [
                next(c for c in channels if c.id == channel_id)
                for channel_id in self.event_data.channel_array_id_list]

            self.plate_type = list({e.plate_type for e in self.electrodes})
            self.electrodes = [e.mappings for e in self.electrodes]

            if len(self.electrodes) == 1:
                self.electrodes = self.electrodes[0]
        elif isinstance(self.channels_tag, StimulationLeds):
            event_data = self.waveform_tag.tag_blocks
            channels = self.channels_tag.led_groups
            self.event_data = next((e for e in event_data if e.id == self.event_data), None)

            if self.event_data is None:
                self.leds = self.channels_tag.led_groups
                self.event_data = StimulationEventData(0, 0, 0, [np.uint16(0)], '')
            else:
                self.leds = [
                    next(c for c in channels if c.id == channel_id)
                    for channel_id in self.event_data.channel_array_id_list]

            if len(self.leds) == 1:
                self.leds = self.leds[0]

    def is_valid(self):
        comp_str = "00000000-0000-0000-0000-000000000000"
        return self.waveform_tag == comp_str and self.channels_tag == comp_str

class StimulationWaveform(Tag):
    # STIMULATIONWAVEFORM Storage element for StimulationEventData, before it
    # is linked to StimulationEvents

    current_version = 0

    def __init__(self, file_id:BufferedReader, rawTag:TagEntry):
        super().__init__(rawTag.tag_guid)

        # Move to the correct location in the file
        start = rawTag.start + TagEntry.BASE_SIZE
        file_id.seek(start, 0)

        version = np.fromfile(file_id, dtype=np.uint16, count=1)[0]

        if version == StimulationWaveform.current_version:
            num_blocks = np.fromfile(file_id, dtype=np.uint16, count=1)[0]

            self.tag_blocks:list[StimulationEventData] = []
            for _ in range(num_blocks):
                id_:np.uint16 = np.fromfile(file_id, dtype=np.uint16, count=1)[0]
                np.fromfile(file_id, dtype=np.uint16, count=1)  # Type: Unused for now
                stim_duration:np.double = np.fromfile(file_id, dtype=np.double, count=1)[0]
                art_elim_duration:np.double = np.fromfile(file_id, dtype=np.double, count=1)[0]
                channel_array_id_list:np.ndarray[np.uint16]\
                    = np.fromfile(file_id, dtype=np.uint16, count=2)
                # Remove all channel array ID's that are 0 - they are placeholders.
                channel_array_id_list = channel_array_id_list[channel_array_id_list!=0]
                description = read_string(file_id)

                self.tag_blocks.append(StimulationEventData(
                    id_, stim_duration, art_elim_duration,
                    channel_array_id_list, description))

            self.micro_ios = read_string(file_id)
        else:
            self.tag_blocks:list[StimulationEventData] = []
            self.micro_ios = ''
            print('StimulationWaveform version not supported')

        if file_id.tell() > (start + rawTag.entry_record.length):
            print('File may be corrupted')

class StimulationLeds(Tag):
    """
    STIMULATIONLEDS File data that enumerates LEDs used in a stimulation
    """
    current_version = 0
    min_array_size = np.int64(20)

    def __init__(self, file_id:BufferedReader, rawTag:TagEntry):
        super().__init__(rawTag.tag_guid)

        # Move to the correct location in the file
        start = rawTag.start + TagEntry.BASE_SIZE

        tag_start = rawTag.start
        tag_end = tag_start + rawTag.entry_record.length
        file_id.seek(start)

        if start < getsize(file_id.name):
            version = np.fromfile(file_id, dtype=np.uint16, count=1)[0]
            if version == StimulationLeds.current_version:
                expected = np.fromfile(file_id, dtype=np.uint16, count=1)[0]
                self.led_groups = []
                array = 1
                pos = np.int64(file_id.tell())

                while (tag_end - pos) >= StimulationLeds.min_array_size:
                    id_ = np.fromfile(file_id, dtype=np.uint32, count=1)[0]
                    plate_type = np.fromfile(file_id, dtype=np.uint32, count=1)[0]
                    num_channels = np.fromfile(file_id, dtype=np.uint32, count=1)[0]
                    channels = [LedPosition(file_id) for _ in range(num_channels)]

                    self.led_groups.append(LedGroup(id_, plate_type, channels))

                    array += 1
                    pos = file_id.tell()

                if expected != np.uint16(len(self.led_groups)):
                    raise ValueError("Encountered an error while loading StimulationLeds: "
                                     f"Expected {expected} groups, got {len(self.led_groups)}")
            else:
                self.led_groups:list[LedGroup] = []
                print('Stimulation LEDs version not supported')
        else:
            raise ValueError("Encountered an error while loading StimulationLeds "
                             f"{rawTag.tag_guid}")

        if file_id.tell() > (tag_start + rawTag.entry_record.length):
            print('File may be corrupted')

class KeyValuePairTag(Tag):
    def __init__(self, file_id:BufferedReader, raw_tag:TagEntry):
        super().__init__(raw_tag.tag_guid)

        start = raw_tag.start + TagEntry.BASE_SIZE
        file_id.seek(start, 0)

        self.key = file_id.read(np.fromfile(file_id, dtype=np.int32, count=1)[0])
        self.key = self.key.decode('utf-8')
        self.value = file_id.read(np.fromfile(file_id, dtype=np.int32, count=1)[0])
        self.value = self.value.decode('utf-8')
        if file_id.tell() > (start + raw_tag.entry_record.length):
            warnings.warn(f"KeyValuePairTag {self.key} may be corrupted, read past expected length")

class ViabilityImpedanceTag(Tag):
    current_version = 0
    def __init__(self, file_id:BufferedReader, raw_tag:TagEntry):
        super().__init__(raw_tag.tag_guid)
        self.creation_date = raw_tag.creation_date
        start = raw_tag.start + TagEntry.BASE_SIZE
        file_id.seek(start, 0)

        # second short is ignored
        version = np.fromfile(file_id, dtype=np.uint16, count=2)[0]
        if version != ViabilityImpedanceTag.current_version:
            raise ValueError(f"ViabilityImpedanceTag version {version} not supported")

        self.measurement_time = DateTime(file_id)
        freq_counts = np.fromfile(file_id, dtype=np.uint32, count=1)[0]
        self.frequencies_count = np.fromfile(file_id, dtype=np.double, count=freq_counts)

        self.channel_array = BasicChannelArray.from_file(file_id)
        if file_id.tell() > (start + raw_tag.entry_record.length):
            warnings.warn("ViabilityImpedanceTag may be corrupted, read past expected length")

        # the matlab implementation theoretically allows for a jagged array here
        # I'm not sure if this intended or just because of bad coding.
        # in case this raises a shape mismatch error, the jagged array is likely intended
        n_channels = len(self.channel_array.channels)
        self.impedances = np.fromfile(file_id, dtype=complex,
                                   count=int(sum(self.frequencies_count*n_channels)))
        self.impedances = self.impedances.reshape((n_channels, freq_counts))

        if file_id.tell() > (start + raw_tag.entry_record.length):
            warnings.warn("ViabilityImpedanceTag may be corrupted, read past expected length")
