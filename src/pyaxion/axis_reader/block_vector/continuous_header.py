from io import BufferedReader

import numpy as np

from ..entries.entry import Entry
from ..entries.entry_record import EntryRecord
from ..helper_functions.crc_32 import CRC32
from ..helper_functions.group_structs import ChannelID
from .combined_header import CombinedBlockVectorHeaderEntry


class ContinuousBlockVectorHeaderEntry(CombinedBlockVectorHeaderEntry):
    def __init__(
        self,
        entry_record: EntryRecord,
        file_id: BufferedReader,
        version_major,
        version_minor,
        data_type,
        sample_type,
        sampling_frequency,
        voltage_scale,
        num_channels_per_block,
        num_datasets_per_block,
        num_samples_per_block,
        vector_header_size,
        block_header_size,
        block_vector_start_time,
        experiment_start_time,
        added_date,
        modified_date,
        duration,
        name,
        description,
        data_region_start,
        data_region_length,
        combined_block_vector_size,
        channel_ids:list[ChannelID],
        dataset_names:list[str],
        size:int
) -> None:
        super().__init__(
            entry_record,
            file_id,
            version_major,
            version_minor,
            data_type,
            sample_type,
            sampling_frequency,
            voltage_scale,
            num_channels_per_block,
            num_datasets_per_block,
            num_samples_per_block,
            vector_header_size,
            block_header_size,
            block_vector_start_time,
            experiment_start_time,
            added_date,
            modified_date,
            duration,
            name,
            description,
            data_region_start,
            data_region_length,
            combined_block_vector_size,
        )
        self.channel_ids = channel_ids
        self.dataset_names = dataset_names
        self.continuous_block_vector_header_entry_size = size + combined_block_vector_size
    
    @classmethod
    def from_file(cls, entry_record:EntryRecord,
                  combined_block_vector:CombinedBlockVectorHeaderEntry,
                  file_id:BufferedReader):
        assert isinstance(combined_block_vector, CombinedBlockVectorHeaderEntry), \
            "Expected combined_block_vector to be an instance of CombinedBlockVectorHeaderEntry"

        start = file_id.tell()

        channel_ids = [ChannelID.from_file(file_id)
                       for _ in range(combined_block_vector.num_channels_per_block)]

        dset_names = [combined_block_vector.num_datasets_per_block]
        dset_name_size_sum = 0

        for i in range(combined_block_vector.num_datasets_per_block):
            dset_name_length = np.fromfile(file_id, dtype=np.int32, count=1)[0]
            dset_names[i] = file_id.read(dset_name_length).decode('utf-8')
            dset_name_size_sum = dset_name_length + dset_name_size_sum

        # calculate and check CRC
        data_size = file_id.tell() - start

        # Calculate and check CRC
        file_id.seek(start)
        crc_bytes = file_id.read(data_size)
        crc_calc = CRC32(CRC32.DefaultPolynomial, CRC32.DefaultSeed).compute(crc_bytes)
        crc_read = np.fromfile(file_id, dtype=np.uint32, count=1)[0]

        assert crc_read == crc_calc, \
            f"BlockVectorMetaData checksum was incorrect: {file_id.name}"

        calc_size = len(channel_ids) * 2 + dset_name_size_sum + len(dset_names) * 4 + 4

        # actual read size
        read_size = file_id.tell() - start

        if calc_size != read_size:
            raise ValueError(f"Unexpected BlockVectorMetadata length in {file_id.name}")
        
        return cls(
            entry_record,
            file_id,
            combined_block_vector.version_major,
            combined_block_vector.version_minor,
            combined_block_vector.data_type,
            combined_block_vector.sample_type,
            combined_block_vector.sampling_frequency,
            combined_block_vector.voltage_scale,
            combined_block_vector.num_channels_per_block,
            combined_block_vector.num_datasets_per_block,
            combined_block_vector.num_samples_per_block,
            combined_block_vector.vector_header_size,
            combined_block_vector.block_header_size,
            combined_block_vector.block_vector_start_time,
            combined_block_vector.experiment_start_time,
            combined_block_vector.added_date,
            combined_block_vector.modified_date,
            combined_block_vector.duration,
            combined_block_vector.name,
            combined_block_vector.description,
            combined_block_vector.data_region_start,
            combined_block_vector.data_region_length,
            combined_block_vector.block_header_size,
            channel_ids,
            dset_names,
            data_size, # size of the additional data read for the continuous block header
        )
