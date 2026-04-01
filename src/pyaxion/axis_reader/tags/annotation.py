from io import BufferedReader

from ..entries.tag_entry import TagEntry
from ..helper_functions.read_string import read_string
from .tag import EventTag


class Annotation(EventTag):
    """Annotation tag that corresponds to events listed in AxIS's play bar"""

    def __init__(self, file_id:BufferedReader, rawTag:TagEntry):
        super().__init__(file_id, rawTag)

        # Assume EventTag constructor leaves us at the right place
        self._well_column = int.from_bytes(file_id.read(1), 'little', signed=False)
        self._well_row = int.from_bytes(file_id.read(1), 'little', signed=False)
        self._electrode_column = int.from_bytes(file_id.read(1), 'little', signed=False)
        self._electrode_row = int.from_bytes(file_id.read(1), 'little', signed=False)

        # Annotations are always broadcast
        if (self._well_column != 0 or self._well_row != 0 or
            self._electrode_column != 0 or self._electrode_row != 0):
            print('File may be corrupted')

        self.note_text = read_string(file_id)

        start = rawTag.start + TagEntry.BASE_SIZE
        if file_id.tell() > (start + rawTag.entry_record.length):
            print('File may be corrupted')
