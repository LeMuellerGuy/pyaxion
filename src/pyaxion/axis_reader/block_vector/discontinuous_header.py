from io import BufferedReader

import numpy as np

from ..entries.entry_record import EntryRecord
from ..helper_functions.crc_32 import CRC32
from ..helper_functions.group_structs import ChannelID
from .combined_header import CombinedBlockVectorHeaderEntry


class DiscontinuousBlockVectorHeaderEntry(CombinedBlockVectorHeaderEntry):
    def __init__(
        self,
        entry_record,
        file_id,
        version_major,
        version_minor,
        data_type,
        sample_type,
        sampling_frequency,
        voltage_scale,
        num_channels_per_block,
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
        channel_ids,
        data_set_name,
        size,
    ):
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
            1, # num_datasets_per_block is always 1 for DiscontinuousBlockVectorHeaderEntry
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
        self.dataset_names = [data_set_name]

    @classmethod
    def from_file(cls, entry_record:EntryRecord,
                 combined_block_header:CombinedBlockVectorHeaderEntry,
                 file_id:BufferedReader) -> None:
        """Deserializes a DiscontinuousBlockVectorHeaderEntry from the given file,
        using the provided combined_block_header for shared header values."""
        # check if aCombinedBlockVector is a
        # CombinedBlockVectorHeaderEntry
        if not isinstance(combined_block_header, CombinedBlockVectorHeaderEntry):
            raise TypeError("combined_block_header must be an instance of" \
            "CombinedBlockVectorHeaderEntry")

        start = file_id.tell()
        n_channels = np.fromfile(file_id, dtype=np.uint32, count=1)[0]
        channel_ids = [ChannelID.from_file(file_id) for _ in range(n_channels)]

        assert combined_block_header.num_datasets_per_block == 1, \
            "Expected num_datasets_per_block to be 1 for DiscontinuousBlockHeaderEntry"

        name_length = np.fromfile(file_id, dtype=np.int32, count=1)[0]
        dset_name = file_id.read(name_length).decode('utf-8')
        # calculate and check CRC
        data_size = file_id.tell() - start

        # Calculate and check CRC
        file_id.seek(start)
        crc_bytes = file_id.read(data_size)
        crc_calc = CRC32(CRC32.DefaultPolynomial, CRC32.DefaultSeed).compute(crc_bytes)
        crc_read = np.fromfile(file_id, dtype=np.uint32, count=1)[0]

        if crc_read != crc_calc:
            raise ValueError(f"BlockVectorMetaData checksum was incorrect: {file_id.name}")

        # channel count + channel array + dataset name length + dataset name + checksum
        calc_size = 4 + len(channel_ids)*2 + 4 + name_length + 4

        # actual read size
        read_size = file_id.tell() - start

        if calc_size != read_size:
            raise ValueError('Unexpected BlockVectorMetadata length')
        return cls(
            entry_record,
            file_id,
            combined_block_header.version_major,
            combined_block_header.version_minor,
            combined_block_header.data_type,
            combined_block_header.sample_type,
            combined_block_header.sampling_frequency,
            combined_block_header.voltage_scale,
            combined_block_header.num_channels_per_block,
            combined_block_header.num_samples_per_block,
            combined_block_header.vector_header_size,
            combined_block_header.block_header_size,
            combined_block_header.block_vector_start_time,
            combined_block_header.experiment_start_time,
            combined_block_header.added_date,
            combined_block_header.modified_date,
            combined_block_header.duration,
            combined_block_header.name,
            combined_block_header.description,
            combined_block_header.data_region_start,
            combined_block_header.data_region_length,
            combined_block_header.block_header_size,
            channel_ids,
            dset_name,
            calc_size,
        )
