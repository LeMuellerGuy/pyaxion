from io import BufferedReader
from typing import TYPE_CHECKING

import numpy as np

from ..entries.entry import Entry

if TYPE_CHECKING:
    from ..entries.entry_record import EntryRecord


class BlockVectorData(Entry):
    """
    BlockVectorData contains instructions for loading the Data types
    from the data portions of the file listed in the header.
    """

    def __init__(
        self,
        aEntryRecord: 'EntryRecord',
        fileID: BufferedReader,
    ):
        super().__init__(aEntryRecord, np.int64(fileID.tell()))
        self.file_id = fileID
        # because python ints are not really limited in size it is no problem to
        # convert a potentially long number to an int here
        self.file_id.seek(int(self.entry_record.length), 1)

        if (
            not (self.file_id.tell() == (self.start + self.entry_record.length))
            or np.isinf(self.entry_record.length)
        ):
            raise ValueError('Unexpected BlockVectorHeader length')
