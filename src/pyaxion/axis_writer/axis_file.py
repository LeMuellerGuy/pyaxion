from pathlib import Path
from typing import Any, Iterable
import numpy as np
from typing_extensions import Buffer
from pyaxion.axis_reader.axis_file import AxisFile
from pyaxion.axis_reader.block_vector.set import BlockVectorSet
from pyaxion.axis_reader.entries.entry_record import EntryRecord
from pyaxion.axis_reader.entries.entry_record_id import EntryRecordID
from pyaxion.axis_reader.helper_functions.crc_32 import CRC32
from pyaxion.axis_reader.Waveforms.Spike_v1 import Spike_v1
from pyaxion.axis_reader.Waveforms.Waveform import Waveform
from pyaxion.axis_writer.entries.Note import WriteNote
from pyaxion.axis_writer.entries.tag import WriteTag


class AxisFileWriter:
    # constansts
    MAGIC_WORD = "AxionBio"
    MAGIC_BETA_FILE = 641                #Preface to Some legacy Axis files
    EXPECTED_NOTES_LENGTH_FIELD = 600    #Number used as a validity check in Axis 1.0 file headers
    
    #Header CRC32 calculation constants
    CRC_POLYNOMIAL = int('edb88320',16)
    CRC_SEED = int('ffffffff',16)
    
    #Header Size Constants, see documentation for details
    PRIMARY_HEADER_CRCSIZE = 1018
    SUBHEADER_CRCSIZE = 1016
    PRIMARY_HEADER_MAXENTRIES = 123
    SUBHEADER_MAXENTRIES = 126
    AXIS_VERSION='2.5.2.1'

    def __init__(self, file_path:Path):
        self.file_path = Path(file_path)
        self.file = open(self.file_path, "wb+")
        self.entry_data_start = 1024
        self.entry_index = 0
        self.entry_data_offset = 0
        self.write_register = {}
        # header
        self.file.write(self.MAGIC_WORD.encode("utf-8"))
        #file.write(b'\x00') # I don't know if we need this byte
        self.file.write(int(1).to_bytes(2, 'little', signed = False))  # data type
        self.file.write(int(1).to_bytes(2, 'little', signed = False))  # major header version
        self.file.write(int(1).to_bytes(2, 'little', signed = False))  # minor header version
        self.file.write(int(0).to_bytes(8, 'little', signed = False))  # notes start, adjusted later
        self.file.write(int(0).to_bytes(4, 'little', signed = False))  # notes length
        self.file.write(int(1024).to_bytes(8, 'little', signed = False))  # entry start
        # The file's header is 34 bytes long + the size of the entry slots + 4 byte checksum
        self.file.seek(34)
        self.file.write(np.zeros(self.PRIMARY_HEADER_MAXENTRIES, dtype=np.uint64).tobytes())
        self.file.write(np.uint32(0).tobytes()) # CRC32 placeholder
        if self.file.tell() < self.entry_data_start:
            # Ensure the file is at least 1024 bytes long
            self.file.write(b'\x00' * int(self.entry_data_start - self.file.tell()))
        assert self.file.tell() == self.entry_data_start, "Header must be 1024 bytes long"

    def WriteData(self, waveform_data:np.ndarray[Any|np.int16]|Iterable[Waveform]|Iterable[Spike_v1],
                  bvs:BlockVectorSet, channels:np.ndarray = None):
        from pyaxion.axis_writer.entries.BlockVector import WriteData
        self.file.seek(0,2)
        WriteData(waveform_data, self, bvs, channels)
        self.entry_data_offset = self.file.tell() - self.entry_data_start

    def WriteEntry(self, entry:EntryRecord):
        """Writes an entry record to the file's entry register between the primary header
        and the entry data. The files writing position is not changed by this operation."""
        if not isinstance(entry, EntryRecord):
            raise TypeError("Entry must be an instance of EntryRecord")
        if self.entry_index >= self.PRIMARY_HEADER_MAXENTRIES:
            raise IndexError("Maximum number of entries reached")
        pos = self.file.tell()
        # Write the entry to the file
        self.file.seek(34 + self.entry_index * 8)
        entry_bytes = entry.to_bytes()
        self.write(entry_bytes)

        # Update the entry index
        self.entry_index += 1
        # Return to the original position
        self.file.seek(pos)

    def CopyNotes(self, file:AxisFile):
        self.file.seek(0,2)
        start = self.file.tell()
        for note in file.Notes:
            WriteNote(note, self)
        
        self.WriteEntry(EntryRecord(
            EntryRecordID.NOTES_ARRAY,
            self.file.tell() - start
        ))
        pos = self.file.tell()
        self.file.seek(14)
        # Update notes start position and length
        self.file.write(np.uint64(start).tobytes())
        self.file.write(np.uint32(len(file.Notes)\
                                 * AxisFileWriter.EXPECTED_NOTES_LENGTH_FIELD).tobytes())
        self.file.seek(pos)
        self.entry_data_offset = pos - self.entry_data_start

    def CopyTags(self, file:AxisFile, copy_all:bool = True):
        self.file.seek(0, 2)
        if copy_all:
            reader = file
        else:
            reader = None
        for tag in file.all_tags.values():
            WriteTag(tag, self, reader)
        self.entry_data_offset = self.file.tell() - self.entry_data_start

    def write(self, buffer:Buffer, /, strict:bool = True):
        # print(f"Writing: {len(buffer)}@{self.file.tell()}")
        if strict:
            assert self.file.tell() not in self.write_register, "Overwriting existing write position"
        self.write_register[self.file.tell()] = len(buffer)
        if self.file is None:
            raise ValueError("File is not open")
        return self.file.write(buffer)

    def tell(self):
        if self.file is None:
            raise ValueError("File is not open")
        return self.file.tell()

    def flush(self):
        if self.file is not None:
            self.file.flush()

    def seek(self, offset:int, whence:int=0):
        if self.file is None:
            raise ValueError("File is not open")
        return self.file.seek(offset, whence)

    def close(self):
        self.file.seek(0)
        # Write the CRC32 of the primary header
        fCRCBytes = self.file.read(self.PRIMARY_HEADER_CRCSIZE)
        crc = CRC32(AxisFile.CRC_POLYNOMIAL, AxisFile.CRC_SEED).compute(fCRCBytes)
        self.file.write(np.uint32(crc).tobytes())
        self.file.close()
        self.file = None

    def __del__(self):
        if self.file is not None:
            self.close()
        self.file = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
        return False
