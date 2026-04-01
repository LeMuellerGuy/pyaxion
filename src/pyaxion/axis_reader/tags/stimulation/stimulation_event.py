from io import BufferedReader

import numpy as np

from ...entries.tag_entry import TagEntry
from ...helper_functions.parse_guid import parse_guid
from ..event_tag import EventTag
from ..tag import Tag
from .channels import StimulationChannels
from .event_data import StimulationEventData
from .leds import StimulationLeds
from .waveform import StimulationWaveform


class StimulationEvent(EventTag):
    # STIMULATIONEVENT Event data that corresponds to a tagged stimulation
    # that occurred in the file

    _currentVersion = 0
    def __init__(self, file_id:BufferedReader, raw_tag:TagEntry):
        super().__init__(file_id, raw_tag)
        # Assume EventTag leaves us at the correct location in the file

        version = np.fromfile(file_id, np.uint16, 1)[0]

        self.electrodes = None
        self.plate_type = None
        self.leds = None

        if version == StimulationEvent._currentVersion:
            # reserved bytes skipped
            _ = np.fromfile(file_id, np.uint16, 1)[0]
            self.waveform_tag = parse_guid(np.fromfile(file_id, np.uint8, 16))
            self.channels_tag = parse_guid(np.fromfile(file_id, np.uint8, 16))

            self.event_data = np.fromfile(file_id, np.uint16, 1)[0]
            self._sequence_number = np.fromfile(file_id, np.uint16, 1)[0]
        else:
            self.waveform_tag = ''
            self.channels_tag = ''
            self.event_data = np.uint16('FFFF')
            self._sequence_number = np.uint16('FFFF')
            print('Stimulation Event version not supported')

        start = raw_tag.start + TagEntry.BASE_SIZE
        if file_id.tell() > (start + raw_tag.entry_record.length):
            print('File may be corrupted')

    def has_valid_tags(self):
        comp_str = "00000000-0000-0000-0000-000000000000"
        return self.waveform_tag == comp_str and self.channels_tag == comp_str

    def link(self, tagMap:dict[str, Tag]):
        if not isinstance(tagMap, dict):
            raise ValueError('Link should be called with a dict')

        if self.waveform_tag in tagMap.keys():
            self.waveform_tag = tagMap[self.waveform_tag]
        else:
            print(f'Missing Stimulation Waveform Tag: {self.waveform_tag}')

        if self.channels_tag in tagMap.keys():
            self.channels_tag = tagMap[self.channels_tag]
        else:
            print(f'Missing Stimulation Channels Tag: {self.channels_tag}')

        if isinstance(self.waveform_tag, StimulationWaveform) and isinstance(self.channels_tag, StimulationChannels):
            event_dates = self.waveform_tag.tag_blocks
            channels = self.channels_tag.channel_groups
            # the next() command returns the first item in the list
            # and is thus equivalent to a matlab construct like
            # arrayA(find(arrayB,1)) where arrayB contains truth values
            self.event_data = next((e for e in event_dates if e.ID == self.event_data), None)
            
            self.electrodes = [
                next(c for c in channels if c.id == channel_id)
                for channel_id in self.event_data.channel_array_id_list]

            self.plate_type = list({e.plate_type for e in self.electrodes})
            self.electrodes = [e.mappings for e in self.electrodes]

            if len(self.electrodes) == 1:
                self.electrodes = self.electrodes[0]
        elif isinstance(self.channels_tag, StimulationLeds):
            event_dates = self.waveform_tag.tag_blocks
            channels = self.channels_tag.led_groups
            self.event_data = next((e for e in event_dates if e.id == self.event_data), None)

            if self.event_data is None:
                self.leds = self.channels_tag.led_groups
                self.event_data = StimulationEventData(0, 0, 0, [np.uint16(0)], '')
            else:
                self.leds = [
                    next(c for c in channels if c.id == channel_id)
                    for channel_id in self.event_data.channel_array_id_list]

            if len(self.leds) == 1:
                self.leds = self.leds[0]
