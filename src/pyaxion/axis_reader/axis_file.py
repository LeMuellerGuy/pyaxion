from io import BufferedReader, open
import warnings

import numpy as np

from pyaxion.axis_reader.block_vector.data import BlockVectorData
from pyaxion.axis_reader.block_vector.header import BlockVectorHeader
from pyaxion.axis_reader.block_vector.header_extension import \
    BlockVectorHeaderExtension
from pyaxion.axis_reader.block_vector.set import BlockVectorSet
from pyaxion.axis_reader.block_vector.combined_header import CombinedBlockVectorHeaderEntry
from pyaxion.axis_reader.block_vector.data_type import BlockVectorDataType
from pyaxion.axis_reader.block_vector.continuous_header import ContinuousBlockVectorHeaderEntry
from pyaxion.axis_reader.block_vector.discontinuous_header import DiscontinuousBlockVectorHeaderEntry
from pyaxion.axis_reader.entries.channel_array import ChannelArray
from pyaxion.axis_reader.entries.entry_record import EntryRecord
from pyaxion.axis_reader.entries.entry_record_id import EntryRecordID
from pyaxion.axis_reader.entries.note import Note
from pyaxion.axis_reader.entries.tag_entry import TagEntry
from pyaxion.axis_reader.helper_functions.crc_32 import CRC32
from pyaxion.axis_reader.tags.tag import (Annotation, LeapInductionEvent,
                                 StimulationEvent, Tag, WellInformation,
                                 KeyValuePairTag, ViabilityImpedanceTag)
from pyaxion.axis_reader.tags.tag_type import TagType
from pyaxion.axis_reader.dataset.dataset import DataSet

def _custom_formatwarning(msg, category, filename, lineno, line=None):
    # Format the warning message without the location and source code
    return f"{category.__name__}: {msg}\n"

# Set the custom formatwarning function
warnings.formatwarning = _custom_formatwarning

class AxisFile:
    """An axion file object containing all the data and metadata from the .raw or .spk file."""
    # constansts
    MAGIC_WORD = "AxionBio"
    MAGIC_BETA_FILE = 641                #Preface to Some legacy Axis files
    EXPECTED_NOTES_LENGTH_FIELD = 600    #Number used as a validity check in Axis 1.0 file headers

    #Header CRC32 calculation constants
    CRC_POLYNOMIAL = int('edb88320',16)
    CRC_SEED = int('ffffffff',16)

    #Header Size Constants, see documentation for details
    PRIMARY_HEADER_CRCSIZE = 1018
    SUBHEADER_CRCSIZE = 1016
    PRIMARY_HEADER_MAXENTRIES = 123
    SUBHEADER_MAXENTRIES = 126
    AXIS_VERSION='2.5.2.1'

    RECORDING_NAME_KEY = 'RecordingName'
    INVESTIGATOR_KEY = 'Investigator'
    DESCRIPTION_KEY = 'Description'

    def __init__(self, file_name:str):

        #AxisFile Opens a new handle to an Axis File
        #  Required arguments:
        #    filename    Pathname of the file to load
        #                Note: Calling with mulitple file names results
        #                in vector of AxisFile objects corresponding to
        #                the input argument file names
        assert file_name is not None
        if not isinstance(file_name, str):
            file_name = str(file_name)

        self.file_name = file_name
        self.file_id = open(file_name,'rb')

        set_map:dict[int, BlockVectorSet] = {}
        self.notes:list[Note] = []
        self.metadata:dict[str, str] = {}

        if not isinstance(self.file_id, BufferedReader):
            raise IOError(f'AxisFile: {file_name} not found.')

        # Make sure that this is a format that we understand
        version_ok = False
        version_warn = False
        # Check for the "magic word" sequence
        magic_read = self.file_id.read(len(AxisFile.MAGIC_WORD)).decode("utf-8").rstrip("\x00")
        if AxisFile.MAGIC_WORD != magic_read:

            # Magic phrase not found -- check to see if this is an old-style file
            if magic_read is not None and np.uint8(magic_read[1]) == AxisFile.MAGIC_BETA_FILE:
                # This looks like a deprecated beta file
                warnings.warn(f"AxisFile version check: File {file_name} looks like a deprecated "
                              "AxIS v0.0 file format, Please Re-record it in Axis to "
                              "update the header data")
                self.file_id.close()
                raise IOError("Axion Py Reader warning: Deprectated axion file types not "
                              "supported. Rerecord the file in the Axion software to "
                              "update the header information.")
            else:
                self.file_id.close()
                raise IOError(f"Fileformat not recognized of file {file_name}")
        else:
            self.primary_data_type:np.uint16 = np.fromfile(self.file_id, np.uint16, 1)[0]
            self.header_version_major:np.uint16 = np.fromfile(self.file_id, np.uint16, 1)[0]
            self.header_version_minor:np.uint16 = np.fromfile(self.file_id, np.uint16, 1)[0]
            self.notes_start:np.uint64 = np.fromfile(self.file_id, np.uint64, 1)[0]
            notes_length:np.uint32 = np.fromfile(self.file_id, np.uint32, 1)[0]

            if notes_length != AxisFile.EXPECTED_NOTES_LENGTH_FIELD:
                raise IOError("Incorrect legacy notes length field")

            if self.header_version_major == 0:
                raise IOError("Axion Py Reader warning: Deprectated axion file types not "
                              "supported. Rerecord the file in the Axion software to "
                              "update the header information.")
                #if self.HeaderVersionMinor == 1:
                #    versionOk = True
                #elif self.HeaderVersionMinor == 2:
                #    versionOk = True

                #self.EntriesStart = np.int64(self.NotesStart)
                #fEntryRecords = LegacySupport.GenerateEntries(self.FileID, self.EntriesStart)

            if self.header_version_major == 1:
                version_ok = True

                self.entries_start = np.fromfile(self.file_id, np.int64, 1)[0]
                entry_slots = np.fromfile(self.file_id, np.uint64,
                                          AxisFile.PRIMARY_HEADER_MAXENTRIES)
                self.entry_records = [EntryRecord.from_uint64(slot) for slot in entry_slots]

                # Check CRC
                self.file_id.seek(0)
                crc_bytes = np.fromfile(self.file_id, np.uint8, AxisFile.PRIMARY_HEADER_CRCSIZE)
                read_crc = np.fromfile(self.file_id, np.uint32, 1)[0]
                calc_crc = CRC32(AxisFile.CRC_POLYNOMIAL, AxisFile.CRC_SEED).compute(crc_bytes)

                if read_crc != calc_crc:
                    raise IOError(f'File header checksum was incorrect: {self.file_name}')

                if self.header_version_minor > 3:
                    version_warn = True

        if not version_ok:
            raise IOError('Unsupported file version'\
                          f'{self.header_version_major}.{self.header_version_minor}')
        if version_warn:
            warnings.warn(f"AxisFile: File {self.file_name} is using a potentially unsupported "\
                 + f"file format version {self.header_version_major}.{self.header_version_minor}.",
                 stacklevel=0)
        # Start Reading Entries
        self.file_id.seek(self.entries_start)

        terminated = False

        tag_entries:list[TagEntry] = []
        current_block_vector_set:BlockVectorSet = None
        # Load file entries from the header
        while not terminated:
            for entry_record in self.entry_records:
                if entry_record.type is EntryRecordID.TERMINATE:
                    terminated = True
                    break

                if entry_record.type is EntryRecordID.CHANNEL_ARRAY:
                    self.channel_array = ChannelArray(entry_record, self.file_id)
                    if current_block_vector_set is not None:
                        if not isinstance(current_block_vector_set.channel_array, ChannelArray):
                            current_block_vector_set.set_values(self.channel_array)
                            # we omit the setmap assignment here because python
                            # stores the objects in the setmap as a reference thus
                            # making a reassignment pointless
                        else:
                            raise ValueError('AxisFile: Only one ChannelArray per BlockVectorSet')

                elif entry_record.type is EntryRecordID.BLOCK_VECTOR_HEADER:
                    current_header = BlockVectorHeader(entry_record, self.file_id)
                    current_block_vector_set = BlockVectorSet(self, current_header)
                    set_map[current_header.first_block] = current_block_vector_set

                elif entry_record.type is EntryRecordID.BLOCK_VECTOR_HEADER_EXTENSION:
                    if isinstance(current_block_vector_set.header_extension,
                                   BlockVectorHeaderExtension):
                        raise ValueError('AxisFile: Only one BlockVectorHeaderExtension ' \
                                         'per BlockVectorSet')
                    current_block_vector_set.set_values(BlockVectorHeaderExtension(
                        entry_record, self.file_id
                    ))
                    # setmap assignment omitted

                elif entry_record.type is EntryRecordID.BLOCK_VECTOR_DATA:
                    data = BlockVectorData(entry_record, self.file_id)
                    # must be none here
                    if isinstance(current_block_vector_set.data, BlockVectorData):
                        raise ValueError('AxisFile: Only one BlockVectorData per BlockVectorSet')

                    target_set = set_map[np.int64(data.start)]
                    if not isinstance(target_set, BlockVectorSet):
                        raise ValueError('AxisFile: No header to match to data')

                    target_set.set_values(data)
                    # setmap assignment omitted

                elif entry_record.type is EntryRecordID.COMBINED_BLOCK_VECTOR_HEADER:
                    # Deserialize CombinedBlockVectorHeaderEntry
                    combined_block_vector = CombinedBlockVectorHeaderEntry.from_file(
                        entry_record, self.file_id)
                    cur_combined_block_vector = None
                    match combined_block_vector.data_type:
                        case BlockVectorDataType.NAMED_CONTINUOUS_DATA:
                            cur_combined_block_vector =\
                                ContinuousBlockVectorHeaderEntry.from_file(
                                entry_record, combined_block_vector, self.file_id)
                        case BlockVectorDataType.SPIKE_V1:
                            cur_combined_block_vector =\
                                DiscontinuousBlockVectorHeaderEntry.from_file(
                                entry_record, combined_block_vector, self.file_id)
                        case _:
                            warnings.warn('Unsupported BlockVectorDataType: %d. Skipping record...',
                                          combined_block_vector.data_type)

                    if cur_combined_block_vector is not None:
                        current_block_vector_set = BlockVectorSet(self, cur_combined_block_vector)

                        # Add ChannelArray to the BlockVectorSet
                        if len(self.channel_array.channels) > 0:
                            local_mappings = [
                                self.channel_array.channels[
                                    self.channel_array.lookup_channel_id(channel_id)]
                                    for channel_id in cur_combined_block_vector.channel_ids]
                            current_block_vector_set.set_values(
                                self.channel_array.get_new_for_channels(local_mappings))

                        set_map[np.int64(cur_combined_block_vector.start)] = \
                            current_block_vector_set

                elif entry_record.type is EntryRecordID.NOTES_ARRAY:
                    # if matlab appends an array it concatenates them
                    for note in Note.parse_array(entry_record, self.file_id):
                        self.notes.append(note)

                elif entry_record.type is EntryRecordID.TAG:
                    tag_entries.append(TagEntry(entry_record, self.file_id))

                else:
                    skip_space = entry_record.length
                    if 0 != self.file_id.seek(skip_space, 1):
                        raise IOError(f"Unable to read rest of file {file_name}")

            if not terminated:
                # Check Magic Bytes
                magic_read = self.file_id.read(len(AxisFile.MAGIC_WORD))
                if AxisFile.MAGIC_WORD != magic_read.decode("utf-8").rstrip("\x00"):
                    raise ValueError(f'Bad sub header magic numbers: {file_name}')

                # Read Entry Records
                entry_slots = np.fromfile(self.file_id, dtype=np.uint64,
                                       count=AxisFile.SUBHEADER_MAXENTRIES)
                self.entry_records = [EntryRecord.from_uint64(slot) for slot in entry_slots]

                # Check CRC of subheader
                self.file_id.seek(
                    (-1 * len(AxisFile.MAGIC_WORD)) - (8 * AxisFile.SUBHEADER_MAXENTRIES), 1)
                crc_bytes = self.file_id.read(AxisFile.SUBHEADER_CRCSIZE)
                read_crc = np.fromfile(self.file_id, dtype=np.uint32, count=1)[0]
                calc_crc = CRC32(AxisFile.CRC_POLYNOMIAL, AxisFile.CRC_SEED).compute(crc_bytes)
                if read_crc != calc_crc:
                    raise ValueError(f'Bad sub header checksum: {file_name}')

                # Skip 4 reserved bytes
                self.file_id.seek(4, 1)

        #Record Final Data Sets
        self.datasets = [DataSet.construct(dset) for dset in set_map.values()]

        #Sort Notes
        self.notes.sort(key = lambda x: x.revision)

        #Collect Tags
        tag_map:dict[str, Tag] = {}
        for entry in tag_entries:
            guid = entry.tag_guid
            if guid in tag_map:
                tag = tag_map[guid]
            else:
                tag = Tag(guid)
                tag_map[guid] = tag

            tag.add_node(entry)

        self.annotations:list[Annotation] = []
        self.plate_map:list[WellInformation] = []
        self.stimulation_events:list[StimulationEvent] = []
        self.leap_induction:list[LeapInductionEvent] = []
        self.well_information:list[WellInformation] = []
        self.calibrations_tags:list[Tag] = []
        self.viability_impedance_events:list[ViabilityImpedanceTag] = []
        self.unlinked_stimulation_events:list[StimulationEvent] = []
        # original: Matlab setmaps' keys are in alphabetical order
        # while python dictionaries are in order of addition
        for key in sorted(tag_map.keys()):
            tag = tag_map[key].promote(self.file_id)
            if isinstance(tag, Annotation):
                self.annotations.append(tag)
            elif isinstance(tag, WellInformation):
                self.plate_map.append(tag)
            elif isinstance(tag, StimulationEvent):
                self.stimulation_events.append(tag)
            elif isinstance(tag, LeapInductionEvent):
                self.leap_induction.append(tag)
            elif isinstance(tag, WellInformation):
                self.well_information.append(tag)
            elif isinstance(tag, KeyValuePairTag):
                self.metadata[tag.key] = tag.value
            elif isinstance(tag, ViabilityImpedanceTag):
                self.viability_impedance_events.append(tag)
            elif isinstance(tag, Tag):
                if tag.type.value == TagType.CALIBRATION_TAG:
                    self.calibrations_tags.append(tag)
                elif tag.type.value == TagType.DELETED:
                    pass
                else:
                    print(f"AxisFile: Unknown tag type {tag.type} for tag {key}")
            tag_map[key] = tag

        if len(self.metadata) == 0 and len(self.notes) > 0:
            self.metadata[self.RECORDING_NAME_KEY] = [note.recording_name for note in self.notes]
            self.metadata[self.INVESTIGATOR_KEY] = [note.investigator for note in self.notes]
            self.metadata[self.DESCRIPTION_KEY] = [note.description for note in self.notes]

        for stim_event in self.stimulation_events:
            if not stim_event.is_valid():
                self.unlinked_stimulation_events.append(stim_event)
            else:
                stim_event.link(tag_map)
        if len(self.unlinked_stimulation_events) > 0:
            warnings.warn(f"{len(self.unlinked_stimulation_events)} unlinked stimulation events "
                          f"found in file {file_name} which were missing metadata.")

        # this needs to be implemented, basically we want the last event created
        # self.leap_induction = sorted(self.leap_induction, key=lambda x: x.CreationDate)[-1]
        self.all_tags = tag_map

    def seek_entry_record(self, entry:EntryRecord):
        """Seeks the file to the given entry record's start position."""
        self.file_id.seek(self.entries_start)
        i = 0
        while self.entry_records[i] is not entry:
            self.file_id.seek(self.entry_records[i].length, 1)
            i += 1
        return self.file_id.tell()
