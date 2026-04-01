from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyaxion.axis_reader.entries.entry_record import EntryRecord

class Entry:
    def __init__(self, entry_record:'EntryRecord'=None, start:int=None) -> None:
        self.entry_record = entry_record
        self.start = start
        # self.indices_for_channels = None
        # self.indices_for_electrodes = None
