import warnings
from ctypes import c_uint64
from typing import Union

import numpy as np

from pyaxion.axis_reader.entries.entry_record_id import EntryRecordID


class EntryRecord:
    LENGTH_MASK_HIGH = c_uint64(int('ffffff', 16))
    LENGTH_MASK_LOW = c_uint64(int('ffffffff', 16))

    @property
    def length(self):
        return self._length
    @length.setter
    def length(self, value:Union[np.uint64, float]):
        if np.isinf(value):
            self._length = np.inf
        else:
            self._length = np.uint64(value)

    def __init__(self, type_:EntryRecordID, length:Union[np.uint64, float]) -> None:
        self.type = type_
        # this is important for end of file entries that
        # where the length reads as infinity
        if np.isinf(length):
            self._length = np.inf
        else: self._length = np.uint64(length)

    @staticmethod
    def from_uint64(value:np.uint64):
        """Generate a EntryRecord instance from an usingned 64 bit integer. 
        The original matlab function can handle an iterable of input values but I decided to
        streamline this function into the python style of returning a single instance

        Args:
            values (np.uint64): The value read from the file

        Returns:
            out (EntryRecord): The EntryRecord instance containing read ID, instruction type, and 
                length of the entry
        """
        assert isinstance(value, np.uint64) or isinstance(value, c_uint64),\
            "Input value must be a np.uint64 or c_uint64"
        value = c_uint64(value)

        # read upper word (with ID field)
        # original code: bitshift(long, int8(8-64)) => int8(8-64) = -56
        # => negative sign flips the shift operator to right shift => right shift by 56 bit
        id_, parsed = EntryRecordID.try_parse(value.value >> 56)
        # Shift right 4 bytes (!) and mask with LENGTH_MASK_HIGH
        # matlab: np.uint64(bitand(bitshift(long, int8(32-64)), EntryRecord.LENGTH_MASK_HIGH))
        length = c_uint64((value.value >> 32) & EntryRecord.LENGTH_MASK_HIGH.value)
        # Check whether it is "Read to end"
        # np.inf conversion
        is_inf = length == EntryRecord.LENGTH_MASK_HIGH
        # Shift left 4 bytes to be andded with lower word
        length = c_uint64(length.value << 32)
        # Read the lower word
        low_word = c_uint64(value.value & EntryRecord.LENGTH_MASK_LOW.value)
        # Finish the check to see if this may be a 'Read to the end'
        # style EntryRecord
        is_inf = is_inf and (low_word == EntryRecord.LENGTH_MASK_LOW)
        # Recombine upper and lower length portions
        length = np.int64(length.value | low_word.value)
        if not parsed:
            warnings.warn(f"Unknown EntryRecordID: {value.value >> 56}")
            id_ = EntryRecordID.SKIP
        if is_inf:
            return EntryRecord(id_, np.inf)
        return EntryRecord(id_, length)

    def to_bytes(self) -> bytes:
        """Convert the EntryRecord to bytes for writing to file.

        Returns:
            bytes: The byte representation of the EntryRecord.
        """
        # Extract the ID and length from the EntryRecord object
        id_ = self.type.value
        length = self.length

        # Check if the length is infinite
        is_inf = length == float('np.inf')

        # Initialize the value as a 64-bit unsigned integer
        value = c_uint64(0)

        # Write the ID into the highest byte
        value.value |= c_uint64(id_).value << 56

        if is_inf:
            # If the length is infinite, set all bits for length
            value.value |= EntryRecord.LENGTH_MASK_HIGH.value << 32
            value.value |= EntryRecord.LENGTH_MASK_LOW.value
        else:
            # Otherwise, write the length into the remaining 8 bytes
            value.value |= int((length & 0xFFFFFFFF00000000) >> np.uint64(32) << np.uint64(32))
            value.value |= int(length & np.uint64(0x00000000FFFFFFFF))
        # Return the value to be written to file
        assert EntryRecord.from_uint64(np.uint64(value)) == self
        return np.uint64(value).tobytes()

    def __eq__(self, other:object) -> bool:
        if not isinstance(other, EntryRecord):
            return False
        return self.type == other.type and self.length == other.length

    def __repr__(self) -> str:
        return f"{self.type.name}: {self.length} bytes"
