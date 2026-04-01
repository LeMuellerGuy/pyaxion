from io import BufferedReader

import numpy as np

from ...entries.tag_entry import TagEntry
from ...helper_functions.group_structs import LedGroup
from ...plate_management.led_position import LedPosition
from ..tag import Tag


class StimulationLeds(Tag):
    """
    STIMULATIONLEDS File data that enumerates LEDs used in a stimulation
    """
    _current_version = 0
    _min_array_size = np.int64(20)

    def __init__(self, file_id:BufferedReader, rawTag:TagEntry):
        super().__init__(rawTag.tag_guid)

        # Move to the correct location in the file
        start = rawTag.start + TagEntry.BASE_SIZE
        seek_result = file_id.seek(start, 'bof')

        tag_start = rawTag.start
        tag_end = tag_start + rawTag.entry_record.length

        if seek_result == 0:
            version = np.fromfile(file_id, dtype=np.uint16, count=1)[0]
            if version == StimulationLeds._current_version:
                expected = np.fromfile(file_id, dtype=np.uint16, count=1)[0]
                self.led_groups = []
                array = 1
                pos = np.int64(file_id.tell())

                while (tag_end - pos) >= StimulationLeds._min_array_size:
                    id_ = np.fromfile(file_id, dtype=np.uint32, count=1)[0]
                    plate_type = np.fromfile(file_id, dtype=np.uint32, count=1)[0]
                    num_channels = np.fromfile(file_id, dtype=np.uint32, count=1)[0]
                    channels = [LedPosition(file_id) for _ in range(num_channels)]

                    self.led_groups.append(LedGroup(id_, plate_type, channels))

                    array += 1
                    pos = file_id.tell()

                if expected != np.uint16(len(self.led_groups)):
                    raise ValueError("Encountered an error while loading StimulationLeds:"\
                                     f"Expected {expected} groups, got {len(self.led_groups)}")
            else:
                self.led_groups:list[LedGroup] = []
                print('Stimulation LEDs version not supported')
        else:
            raise ValueError("Encountered an error while loading"\
                             f"StimulationLeds {rawTag.tag_guid}")

        if file_id.tell() > (tag_start + rawTag.entry_record.length):
            print('File may be corrupted')
