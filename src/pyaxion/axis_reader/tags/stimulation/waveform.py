from io import BufferedReader

import numpy as np

from ...entries.tag_entry import TagEntry
from ...helper_functions.read_string import read_string
from ..tag import Tag
from .event_data import StimulationEventData


class StimulationWaveform(Tag):
    # STIMULATIONWAVEFORM Storage element for StimulationEventData, before it
    # is linked to StimulationEvents

    _currentVersion = 0

    def __init__(self, fileID:BufferedReader, rawTag:TagEntry):
        super().__init__(rawTag.tag_guid)

        # Move to the correct location in the file
        start = rawTag.start + TagEntry.BASE_SIZE
        fileID.seek(start, 0)

        version = np.fromfile(fileID, dtype=np.uint16, count=1)[0]


        if version == StimulationWaveform._currentVersion:
            num_blocks = np.fromfile(fileID, dtype=np.uint16, count=1)[0]  # Reserved short

            self.tag_blocks:list[StimulationEventData] = []
            for _ in range(num_blocks):
                id_:np.uint16 = np.fromfile(fileID, dtype=np.uint16, count=1)[0]
                np.fromfile(fileID, dtype=np.uint16, count=1)  # Type: Unused for now
                stim_duration:np.double = np.fromfile(fileID, dtype=np.double, count=1)[0]
                art_elim_duration:np.double = np.fromfile(fileID, dtype=np.double, count=1)[0]
                channel_array_id_list:np.ndarray[np.uint16] = np.fromfile(
                    fileID, dtype=np.uint16, count=2)
                # Remove all channel array ID's that are 0 - they are placeholders.
                channel_array_id_list = channel_array_id_list[channel_array_id_list!=0]
                description = read_string(fileID)

                self.tag_blocks.append(StimulationEventData(
                    id_, stim_duration, art_elim_duration,
                    channel_array_id_list, description))

            self.micro_ops = read_string(fileID)
        else:
            self.tag_blocks:list[StimulationEventData] = []
            self.micro_ops = ''
            print('StimulationWaveform version not supported')

        if fileID.tell() > (start + rawTag.entry_record.length):
            print('File may be corrupted')
