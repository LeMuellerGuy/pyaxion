from io import BufferedReader

import numpy as np

from ..entries.tag_entry import TagEntry
from ..helper_functions.date_time import DateTime
from ..plate_management.channel_mapping import ChannelMapping
from .tag import Tag


class LeapInductionEvent(Tag):
    """
    LEAPINDUCTIONEVENT Tag that describes a LEAP induction event
    """

    current_version = 0

    def __init__(self, file_id:BufferedReader, raw_tag:TagEntry):
        super().__init__(raw_tag.tag_guid)

        start = raw_tag.start + TagEntry.BASE_SIZE
        seek_result = file_id.seek(start, 0)

        if seek_result == 0:

            version = np.fromfile(file_id, dtype=np.uint16, count=2)
            version = version[0]  # Second short is ignored

            if version != LeapInductionEvent.current_version:
                raise ValueError('Unknown LEAP induction event version')

            self.leap_induction_start_time = DateTime(file_id)

            ticks = np.fromfile(file_id, dtype=np.uint64, count=1)[0]
            self.leap_induction_duration = np.double(ticks) * 1e-7

            self.plateType:np.uint32 = np.fromfile(file_id, dtype=np.uint32, count=1)[0]
            num_channels = np.fromfile(file_id, dtype=np.uint32, count=1)[0]

            self.leaped_channels = [ChannelMapping.from_file(file_id) for _ in range(num_channels)]

        else:
            raise ValueError(f'Encountered an error while loading '
                             f'LeapInductionEvent {raw_tag.tag_guid}')

        start = raw_tag.start + TagEntry.BASE_SIZE
        if file_id.tell() > (start + raw_tag.entry_record.length):
            print('File may be corrupted')
