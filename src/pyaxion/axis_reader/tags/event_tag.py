from io import BufferedReader

import numpy as np

from ..entries.tag_entry import TagEntry
from .tag import Tag


class EventTag(Tag):
    """
    EventTag base class for tagged events in the file. Indicates
    time stamps for particular events"""

    def __init__(self, fileID:BufferedReader, rawTag:TagEntry):
        super().__init__(rawTag.tag_guid)

        start = rawTag.start + TagEntry.BASE_SIZE
        seek_result = fileID.seek(start)

        if seek_result == 0:
            self.sampling_frequency = np.fromfile(fileID, np.double, 1)[0]
            self.event_time_sample = np.fromfile(fileID, np.int64, 1)[0]
            self.event_duration_samples = np.fromfile(fileID, np.int64, 1)[0]

            self.event_time = np.double(self.event_time_sample / self.sampling_frequency)
        else:
            raise ValueError(f'Encountered an error while loading EventTag {rawTag.tag_guid}')
