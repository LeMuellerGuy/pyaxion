from enum import Enum

from numpy import uint8


class EntryRecordID(Enum):
    """Enum identifying the type of an entry in an Axis file."""
    # commented are the hex numbers
    TERMINATE = uint8(0) # 00
    SKIP = uint8(255) # ff
    NOTES_ARRAY = uint8(1) # 01
    CHANNEL_ARRAY = uint8(2) # 02
    BLOCK_VECTOR_HEADER = uint8(3) # 03
    BLOCK_VECTOR_DATA = uint8(4) # 04
    BLOCK_VECTOR_HEADER_EXTENSION = uint8(5) # 05
    TAG = uint8(6) # 06
    COMBINED_BLOCK_VECTOR_HEADER = uint8(7) # 07

    @classmethod
    def try_parse(cls, value:int) -> tuple['EntryRecordID', bool]:
        try:
            val = cls(value)
            return (val, True)
        except Exception as e:
            print(f"EntryRecordID Warning: Failed to parse value {value} with exception {e}")
            return (value, False)
