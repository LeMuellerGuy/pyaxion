from io import BufferedReader

import numpy as np

from ..entries.entry import Entry
from ..entries.entry_record import EntryRecord
from ..helper_functions.crc_32 import CRC32
from ..helper_functions.date_time import DateTime


class CombinedBlockVectorHeaderEntry(Entry):
    base_size_in_bytes = 120
    def __init__(self, entry_record:EntryRecord, file_id:BufferedReader,
                 version_major, version_minor, data_type, sample_type, sampling_frequency,
                 voltage_scale, num_channels_per_block, num_datasets_per_block,
                 num_samples_per_block, vector_header_size, block_header_size,
                 block_vector_start_time, experiment_start_time, added_date,
                 modified_date, duration, name, description, data_region_start,
                 data_region_length, size) -> None:
        super().__init__(entry_record, file_id.tell())
        self.version_major = version_major
        self.version_minor = version_minor
        self.data_type = data_type
        self.sample_type = sample_type
        self.sampling_frequency = sampling_frequency
        self.voltage_scale = voltage_scale
        self.num_channels_per_block = num_channels_per_block
        self.num_datasets_per_block = num_datasets_per_block
        self.num_samples_per_block = num_samples_per_block
        self.vector_header_size = vector_header_size
        self.block_header_size = block_header_size
        self.block_vector_start_time = block_vector_start_time
        self.experiment_start_time = experiment_start_time
        self.added_date = added_date
        self.modified_date = modified_date
        self.duration = duration
        self.name = name
        self.description = description
        self.data_region_start = data_region_start
        self.data_region_length = data_region_length
        self.size = size

    @classmethod
    def from_file(cls, entry_record:EntryRecord, file_id:BufferedReader):
        pos = file_id.tell()
        version_major = np.fromfile(file_id, dtype=np.uint16, count=1)[0]
        version_minor = np.fromfile(file_id, dtype=np.uint16, count=1)[0]

        data_type = np.fromfile(file_id, dtype=np.uint16, count=1)[0]
        sample_type = np.fromfile(file_id, dtype=np.uint16, count=1)[0]
        sampling_frequency = np.fromfile(file_id, dtype=np.float64, count=1)[0]
        voltage_scale = np.fromfile(file_id, dtype=np.float64, count=1)[0]

        num_channels_per_block = np.fromfile(file_id, dtype=np.uint32, count=1)[0]
        num_datasets_per_block = np.fromfile(file_id, dtype=np.uint32, count=1)[0]
        num_samples_per_block = np.fromfile(file_id, dtype=np.uint32, count=1)[0]

        vector_header_size = np.fromfile(file_id, dtype=np.uint32, count=1)[0]
        block_header_size = np.fromfile(file_id, dtype=np.uint32, count=1)[0]

        block_vector_start_time = DateTime(file_id)
        experiment_start_time = DateTime(file_id)
        added_date = DateTime(file_id)
        modified_date = DateTime(file_id)

        if version_major > 1 or version_minor >= 1:
            duration = np.fromfile(file_id, dtype=np.float64, count=1)[0]
        else:
            duration = None

        name_string_bytes = np.fromfile(file_id, dtype=np.int32, count=1)[0]
        name = file_id.read(name_string_bytes).decode('utf-8')
        description_string_bytes = np.fromfile(file_id, dtype=np.int32, count=1)[0]
        description = file_id.read(description_string_bytes).decode('utf-8')

        data_region_start = np.fromfile(file_id, dtype=np.int64, count=1)[0]
        data_region_length = np.fromfile(file_id, dtype=np.int64, count=1)[0]

        #CRC Check
        data_size = file_id.tell() - pos
        file_id.seek(pos)
        crc_bytes = file_id.read(data_size)
        crc_calc = CRC32(CRC32.DefaultPolynomial, CRC32.DefaultSeed).compute(crc_bytes)
        crc_read = np.fromfile(file_id, dtype=np.uint32, count=1)[0]

        assert crc_calc == crc_read, \
            f"CRC check failed for CombinedBlockVectorHeaderEntry at position {pos}. "\
                f"Expected {crc_read}, got {crc_calc}."

        size = CombinedBlockVectorHeaderEntry.base_size_in_bytes \
            + name_string_bytes\
            + description_string_bytes + 8
        if version_major > 1 or version_minor >= 1:
            size += 8 # add duration field

        assert size == (file_id.tell() - pos), \
            f"Unexpected CombinedBlockVectorHeaderEntry length at position {pos}. "\
                f"Expected {size}, got {file_id.tell() - pos}."

        return cls(entry_record, file_id, version_major, version_minor, data_type,
                   sample_type, sampling_frequency, voltage_scale, num_channels_per_block,
                   num_datasets_per_block, num_samples_per_block, vector_header_size,
                   block_header_size, block_vector_start_time, experiment_start_time,
                   added_date, modified_date, duration, name, description,
                   data_region_start, data_region_length, size)
