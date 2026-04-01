from io import BufferedReader

import numpy as np

from .entry import Entry
from .entry_record import EntryRecord
from .entry_record_id import EntryRecordID
from ..helper_functions.date_time import DateTime

class Note(Entry):
    """
    Container class for Axis File notes.
    
    Properties:
        - investigator: Text data taken from 'Investigator' field of the Axis GUI.
        - recording_name: Text data taken from 'Recording Name' field of the Axis GUI.
        - description: Text data taken from 'Description' field of the Axis GUI.
        - revision: Number of revisions this note has experienced.
        - revision_date: Date this note was last revised.
    """

    SIZE = 618

    _recording_name_offset = 50
    _description_offset = 100
    _revision_offset = 600
    _investigator_offset = 50
    _recording_name_length = 50
    _description_length = 500

    def __init__(self, aEntryRecord, file_id:BufferedReader):
        super().__init__(aEntryRecord, file_id.tell())

        if not aEntryRecord:
            return

        # Assume utf-8 encoding for reading text fields
        self.investigator = file_id.read(Note._investigator_offset).decode('utf-8')\
            .strip().rstrip("\x00")
        self.investigator = self.investigator.replace('\r', '')

        file_id.seek(self.start + Note._recording_name_offset)
        self.recording_name = file_id.read(Note._recording_name_length).decode('utf-8')\
            .strip().rstrip("\x00")
        self.recording_name = self.recording_name.replace('\r', '')

        file_id.seek(self.start + Note._description_offset)
        self.description = file_id.read(Note._description_length).decode('utf-8')\
            .strip().rstrip("\x00")
        self.description = self.description.replace('\r', '')

        file_id.seek(self.start + Note._revision_offset)
        self.revision:np.uint32 = np.fromfile(file_id, dtype=np.uint32, count=1)[0]
        self.revision_date = DateTime(file_id)

        if file_id.tell() != (self.start + self.entry_record.length):
            raise ValueError('Unexpected BlockVectorHeader length')

    @staticmethod
    def parse_array(entry_record:EntryRecord, file_id:BufferedReader):
        count = int(entry_record.length // Note.SIZE)
        array = np.empty(count, dtype=Note)
        for i in range(count):
            entry_record = EntryRecord(EntryRecordID.NOTES_ARRAY, Note.SIZE)
            array[i] = Note(entry_record, file_id)
        return array
