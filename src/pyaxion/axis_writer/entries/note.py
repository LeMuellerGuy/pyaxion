from typing import TYPE_CHECKING
from pyaxion.axis_reader.entries.Note import Note
from pyaxion.axis_writer.entries.DateTime import WriteDateTime
if TYPE_CHECKING:
    from pyaxion.axis_writer.axis_file import AxisFileWriter

RECORDING_NAME_OFFSET = 50
DESCRIPTION_OFFSET = 100
REVISION_OFFSET = 600
INVESTIGATOR_LENGTH = 50
RECORDING_NAME_LENGTH = 50
DESCRIPTION_LENGTH = 500

def WriteNote(note: Note, file:'AxisFileWriter'):
    """
    Container class for Axis File notes.

    Properties:
        - Investigator: Text data taken from 'Investigator' field of the Axis GUI.
        - RecordingName: Text data taken from 'Recording Name' field of the Axis GUI.
        - Description: Text data taken from 'Description' field of the Axis GUI.
        - Revision: Number of revisions this note has experienced.
        - RevisionDate: Date this note was last revised.
    """

    # Write Investigator
    investigator_bytes = note.Investigator.encode('utf-8')[:INVESTIGATOR_LENGTH]
    investigator_bytes += b'\x00' * (INVESTIGATOR_LENGTH - len(investigator_bytes))
    file.write(investigator_bytes)

    # Write RecordingName
    recording_name_bytes = note.RecordingName.encode('utf-8')[:RECORDING_NAME_LENGTH]
    recording_name_bytes += b'\x00' * (RECORDING_NAME_LENGTH - len(recording_name_bytes))
    file.write(recording_name_bytes)

    # Write Description
    description_bytes = note.Description.encode('utf-8')[:DESCRIPTION_LENGTH]
    description_bytes += b'\x00' * (DESCRIPTION_LENGTH - len(description_bytes))
    file.write(description_bytes)

    # Write Revision
    file.write(note.Revision.tobytes())

    # Write RevisionDate
    WriteDateTime(note.RevisionDate, file)
