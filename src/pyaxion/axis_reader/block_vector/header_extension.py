from io import BufferedReader

import numpy as np

from ..entries.entry import Entry
from ..entries.entry_record import EntryRecord
from ..helper_functions.date_time import DateTime
from .data_type import BlockVectorDataType


class BlockVectorHeaderExtension(Entry):
    """Extensions to the header that provides additional metadata about the block vector."""
    _maxNameChar = 50
    def __init__(self, entryRecord: EntryRecord, fileID:BufferedReader) -> None:
        super().__init__(entryRecord, fileID.tell())
        self.extension_version_major:np.uint16 = np.fromfile(fileID, np.uint16, 1)[0]
        self.extension_version_minor:np.uint16 = np.fromfile(fileID, np.uint16, 1)[0]
        self.data_type, _ = BlockVectorDataType.try_parse(np.fromfile(fileID, np.uint16, 1)[0])
        self.added = DateTime(fileID)
        self.modified = DateTime(fileID)
        self.name = fileID.read(BlockVectorHeaderExtension._maxNameChar)
        self.name = self.name.decode('utf-8').rstrip("\x00")
        self.description = fileID.read(self.start + int(self.entry_record.length) - fileID.tell())
        self.description = self.description.decode('utf-8').rstrip("\x00")
