from io import BufferedReader

from numpy import float64, fromfile, int64, uint32

from pyaxion.axis_reader.entries.entry import Entry
from pyaxion.axis_reader.entries.entry_record import EntryRecord
from pyaxion.axis_reader.entries.entry_record_id import EntryRecordID
from pyaxion.axis_reader.helper_functions.date_time import DateTime


class BlockVectorHeader(Entry):
    """
    BlockVectorHeader Primary data regarding a BlockVectorSet of Data
    This class contains the basic information about an entry of 
    Block Vector Data that is necessary to load it as a series of
    vectors. 
    
    - SamplingFrequency:    Recording sampling rate (in Hz) of the data
    - VoltageScale:         Voltage (in Volts) of the conversion factor
                            from the stored int16's in the Data vectors
                            to a real voltage value. i.e. Signal =
                            double(VoltageScale) * Waveform.Data
    - FileStartTime:        DateTime (See DateTime.m) when this
                            recording started
    - ExperimentStartTime:  DateTime (See DateTime.m) when the
                            device that acquired this data started
                            aquiring
    - FirstBlock:           Pointer (# of bytes frome the beginning of
                            the file) to the start of the associated
                            BlockVectorData entry
    - NumChannelsPerBlock:  Number of Channels of data stored in every
                            block of the data.
    - NumSamplesPerBlock:   Number of samples in every channel-wise
                            vector of the block.
    - BlockHeaderSize:      Number of bytes used for header of each
                            block.
    
    """
    SIZE = 64
    def __init__(
        self,
        entryRecord: EntryRecord,
        fileID: BufferedReader,
    ):
        super().__init__(entryRecord, int64(fileID.tell()))

        self.sampling_frequency:float64 = fromfile(fileID, dtype= float64, count=1)[0]
        self.voltage_scale:float64 = fromfile(fileID, dtype=float64, count=1)[0]
        self.file_start_time = DateTime(fileID)
        self.experiment_start_time = DateTime(fileID)
        self.first_block:int64 = fromfile(fileID, dtype= int64, count=1)[0]
        self.num_channels_per_block:uint32 = fromfile(fileID, dtype= uint32, count=1)[0]
        self.num_samples_per_block:uint32 = fromfile(fileID, dtype=uint32, count=1)[0]
        self.block_header_size:uint32 = fromfile(fileID, dtype=uint32, count=1)[0]

        if (
            self.entry_record.length != -1
            and fileID.tell() != (self.start + self.entry_record.length)
        ):
            raise ValueError('Unexpected BlockVectorHeader length')

    @staticmethod
    def generate(
        file_id,
        sampling_frequency,
        voltage_scale,
        file_start_time,
        experiment_start_time,
        first_block:int,
        n_channels_per_block:int,
        n_samples_per_block:int,
        block_header_size:int,
    ):
        """Generates a BlockVectorHeader and a corresponding entry record for the given values."""
        bvh = BlockVectorHeader(
            EntryRecord(EntryRecordID.BLOCK_VECTOR_HEADER, -1),
            file_id,
        )
        bvh.sampling_frequency = sampling_frequency
        bvh.voltage_scale = voltage_scale
        bvh.file_start_time = file_start_time
        bvh.experiment_start_time = experiment_start_time
        bvh.first_block = first_block
        bvh.num_channels_per_block = n_channels_per_block
        bvh.num_samples_per_block = n_samples_per_block
        bvh.block_header_size = block_header_size
        return bvh
