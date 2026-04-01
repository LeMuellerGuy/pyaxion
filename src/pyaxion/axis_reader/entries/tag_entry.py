from enum import Enum
from io import BufferedReader

import numpy as np

from ..helper_functions.date_time import DateTime
from ..helper_functions.parse_guid import parse_guid
from ..entries.entry import Entry
from ..entries.entry_record import EntryRecord


class TagType(Enum):
    """Enumerates the available tag types in an Axis file."""
    DELETED = 0
    """Tag revision where this TagGUID has been deleted.
    This is a special case, Tags may alternate between this type and their own as the
    are deleted / undeleted"""
    WELL_TREATMENT = np.uint16(1)
    """Describes the treatment state of a well in a file"""
    USER_ANNOTATION = np.uint16(2)
    """Time based note added to the file by the user"""
    SYSTEM_ANNOTATION = np.uint16(3)
    """Time based note added to the file by Axis"""
    DATA_LOSS_EVENT = np.uint16(4)
    """Tag that records any loss of data in the system that affects this recorded file.
    Remarks: Coming soon, Currently Unused!"""
    STIMULATION_EVENT = np.uint16(5)
    """Tag that describes a stimulation that was applied to the plate during recording"""
    STIMULATION_CHANNEL_GROUP = np.uint16(6)
    """Tag that lists the channels that were loaded for stimulation for a StimulationEvent
    Many StimulationEvent tags may reference the same StimulationChannelGroup"""
    STIMULATION_WAVEFORM = np.uint16(7)
    """Tag that lists the stimulation that was applied for stimulation for a StimulationEvent
    Many StimulationEvent tags may reference the same StimulationWaveform"""
    CALIBRATION_TAG = np.uint16(8)
    """Tag that is used for axis's internal calibration of noise measurements. May not be work
    as expected, as it is not supported by the matlab implementation."""
    STIMULATION_LED_GROUP = np.uint16(9)
    """Tag that lists the LEDs that were loaded for stimulation for a StimulationEvent
    Many StimulationEvent tags may reference the same StimulationLedGroup"""
    DOSE_EVENT = np.uint16(10)
    """(Unsupported in in this library)"""
    STRING_DICTIONARY_PAIR = np.uint16(11)
    """A metadata tag and its associated value."""
    LEAP_INDUCTION_PAIR = np.uint16(12)
    """Tag marking a LEAP induction event for a plate/recording"""
    VIABILITY_IMPEDANCE_EVENT = np.uint16(13)
    """Tag for acquiring viability data"""

class TagEntry(Entry):
    """
    Section of an AxisFile that contains TagRevision.
    """

    BASE_SIZE = np.int64(2 + DateTime.Size + 16 + 4)

    def __init__(self, entryRecord:EntryRecord, fileID:BufferedReader):
        super().__init__(entryRecord, np.int64(fileID.tell()))
        type_short = np.fromfile(fileID, dtype=np.uint16, count=1)[0]
        try:
            self.type = TagType(type_short)
        except ValueError:
            print(f"Unknown tag type {type_short} will be ignored")
            self.type = TagType.DELETED

        self.creation_date = DateTime(fileID)
        guid_bytes = np.fromfile(fileID, dtype=np.uint8, count=16)
        self.tag_guid = parse_guid(guid_bytes)
        self.revision_number:np.uint32 = np.fromfile(fileID, dtype=np.uint32, count=1)[0]

        # matlab code has "cof" which should translate to __whence = 1 for current location
        # the data of the tag is appended to the entry and is skipped here to be read
        # in later
        fileID.seek(int(self.entry_record.length) - TagEntry.BASE_SIZE, 1)

    def __repr__(self):
        return f"{self.type.name}: {self.tag_guid}"
