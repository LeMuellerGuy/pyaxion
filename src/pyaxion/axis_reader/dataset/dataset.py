from abc import abstractmethod
from typing import Iterable, Literal, Union

import numpy as np

from ..block_vector.combined_header import CombinedBlockVectorHeaderEntry
from ..block_vector.data_type import BlockVectorDataType
from ..block_vector.sample_type import BlockVectorSampleType
from ..block_vector.set import BlockVectorSet, ReturnDimension
from ..entries.channel_array import ChannelArray, ChannelMapping
from ..plate_management.plate_types import PlateTypes


class DataSet:
    """Container for metadata and data of each dataset in an Axis file."""
    @classmethod
    def construct(cls, vector_set:'BlockVectorSet' = None):
        """Constructs a new `DataSet` instance from the given `BlockVectorSet`,
        returning a subclass of `DataSet` depending on the data type of the `BlockVectorSet`."""
        # has to be imported here to avoid circular imports.
        from .continuous_dataset import \
            ContinuousDataSet  # pylint: disable=import-outside-toplevel
        from .spike_dataset import \
            SpikeDataSet  # pylint: disable=import-outside-toplevel
        instance = cls(vector_set)
        if vector_set is not None:
            match instance.data_type:
                case BlockVectorDataType.RAW_V1:
                    return ContinuousDataSet(instance)
                case BlockVectorDataType.SPIKE_V1:
                    return SpikeDataSet(instance, vector_set.combined_block_vector)
                case BlockVectorDataType.NAMED_CONTINUOUS_DATA:
                    return ContinuousDataSet(instance, vector_set.combined_block_vector)
                case _:
                    raise ValueError(f"Unsupported BlockVectorDataType {instance.data_type}")
        return instance

    def __init__(self, vector_set:'DataSet|BlockVectorSet' = None):
        try:
            self.dataset_names = vector_set.dataset_names
        except AttributeError:
            self.dataset_names = []
        if vector_set is None:
            self.file_id = None
            self.source_file = None
            self.version_major = None
            self.version_minor = None
            self.data_type = None
            self.sample_type = None
            self.vector_header_size = None
            self.block_header_size = None
            self.num_channels_per_block = None
            self.num_datasets_per_block = None
            self.num_samples_per_block = None
            self.data_region_start = None
            self.data_region_length = None
            self.name = None
            self.description = None
            self.sampling_frequency = None
            self.voltage_scale = None
            self.block_vector_start_time = None
            self.experiment_start_time = None
            self.added_date = None
            self.modified_date = None
            self.channel_array = ChannelArray()
            return
        if isinstance(vector_set, DataSet):
            self.file_id = vector_set.file_id
            self.source_file = vector_set.source_file
            self.version_major = vector_set.version_major
            self.version_minor = vector_set.version_minor
            self.data_type = vector_set.data_type
            self.sample_type = vector_set.sample_type
            self.vector_header_size = vector_set.vector_header_size
            self.block_header_size = vector_set.block_header_size
            self.num_channels_per_block = vector_set.num_channels_per_block
            self.num_datasets_per_block = vector_set.num_datasets_per_block
            self.num_samples_per_block = vector_set.num_samples_per_block
            self.data_region_start = vector_set.data_region_start
            self.data_region_length = vector_set.data_region_length
            self.name = vector_set.name
            self.description = vector_set.description
            self.sampling_frequency = vector_set.sampling_frequency
            self.voltage_scale = vector_set.voltage_scale
            self.block_vector_start_time = vector_set.block_vector_start_time
            self.experiment_start_time = vector_set.experiment_start_time
            self.added_date = vector_set.added_date
            self.modified_date = vector_set.modified_date
            self.channel_array = vector_set.channel_array
            return
        if isinstance(vector_set, BlockVectorSet):
            self.source_file = vector_set.source_file
            self.file_id = vector_set.source_file.file_id
            if isinstance(vector_set.combined_block_vector, CombinedBlockVectorHeaderEntry):
                channel_array = vector_set.channel_array
                cbv = vector_set.combined_block_vector

                self.channel_array = channel_array
                self.version_major = cbv.version_major
                self.version_minor = cbv.version_minor
                self.data_type = cbv.data_type
                self.sample_type = cbv.sample_type
                self.vector_header_size = cbv.vector_header_size
                self.block_header_size = cbv.block_header_size
                self.num_channels_per_block = cbv.num_channels_per_block
                self.num_datasets_per_block = cbv.num_datasets_per_block
                self.num_samples_per_block = cbv.num_samples_per_block
                self.data_region_start = cbv.data_region_start
                self.data_region_length = cbv.data_region_length
                self.name = cbv.name
                self.description = cbv.description
                self.sampling_frequency = cbv.sampling_frequency
                self.voltage_scale = cbv.voltage_scale
                self.block_vector_start_time = cbv.block_vector_start_time
                self.experiment_start_time = cbv.experiment_start_time
                self.added_date = cbv.added_date
                self.modified_date = cbv.modified_date
            else:
                header = vector_set.header
                header_extension = vector_set.header_extension

                self.channel_array = vector_set.channel_array
                self.vector_header_size = 0
                self.num_datasets_per_block = 1
                self.sample_type = BlockVectorSampleType.INT16

                self.block_header_size = header.block_header_size
                self.num_channels_per_block = header.num_channels_per_block
                self.num_samples_per_block = header.num_samples_per_block
                self.sampling_frequency = header.sampling_frequency
                self.voltage_scale = header.voltage_scale
                self.block_vector_start_time = header.file_start_time
                self.experiment_start_time = header.experiment_start_time
                self.data_region_start = vector_set.data.start
                self.data_region_length = vector_set.data.entry_record.length

                if header_extension is not None:
                    self.version_major = header_extension.extension_version_major
                    self.version_minor = header_extension.extension_version_minor
                    self.data_type = header_extension.data_type
                    self.name = header_extension.name
                    self.description = header_extension.description
                    self.added_date = header_extension.added
                    self.modified_date = header_extension.modified
                else:
                    self.version_major = 0
                    self.version_minor = 0
                    self.data_type = BlockVectorDataType.RAW_V1
                    self.name = None
                    self.description = None
                    self.added_date = None
                    self.modified_date = None

    @property
    def num_bytes_per_block(self):
        """Number of bytes per block."""
        return self.block_header_size+self.num_datasets_per_block*self.num_channels_per_block\
            *self.num_samples_per_block*BlockVectorSampleType.get_size_in_bytes(self.sample_type)

    @property
    def num_blocks(self):
        """Number of blocks in the dataset."""
        return self.data_region_length//self.num_bytes_per_block

    @abstractmethod
    def load_data(self, well:str|None = None, electrode:Iterable[int]|None = None,
                timespan:Iterable[int]|None = None,
                dimension:ReturnDimension = ReturnDimension.DEFAULT,
                subsampling_factor:float = 1):
        """
        Loads contained data returning a numpy array of Waveforms where the dimensions
            depend on the input.

        Args:
            well (str | None): Comma delimited string of well IDs or None. 
                Defaults to None, loading all available wells.
    
            electrode (Iterable[int] | None): int iterable containing the channels
                (i.e. electrodes) to load or None. Defaults to None, loading all electrodes.
                Remember that electrodes are enumerated as a combination of their row and column
                index, e.g. 11, 12, 13, ...

            timespan (Iterable[int] | None): int iterable of 2 elements (more will be ignored)
                representing the time in SECONDS as [start, stop] range or None. Defaults to None,
                loading all timepoints. Start of recording is always 0.
        
            dimension (ReturnDimension): int value as defined in the ReturnDimension Enum:
                - DEFAULT = 0:      5 if data is waveform or 3 if data is spike only.
                - BYPLATE = 1:      returns a 1D array of Waveform objects, 1 Waveform
                                    per signal in the plate
                - BYWELL = 3:       2D array of Waveform objects containg multiple electrodes at
                                    once with dimensions (well Rows) x (well Columns)
                - BYELECTRODE = 5:  4D array of Waveform objects with dimensions
                (well Rows) x (well Columns) x (electrode Columns) x (electrode Rows)
            
            subsampling_factor (float): float value determining the rate of subsampling.
                Subsampling is performed by omitting values.

        Note: The class is fully "backwards" compatible with the original matlab argument
            interpretation but I chose to make the typing more clear and simplify the arguments.
        """

    @staticmethod
    # determine the typing for the arguments. I assume it should
    # be uint8 because that is what the other functions return
    def all_wells_electrodes(columns: list[int], rows: list[int]) -> np.ndarray[np.uint8]:
        """Returns a 2D array of all combinations of the given columns and rows,
        sorted ascending and deduplicated."""
        columns = sorted(set(columns))  # sort ascending and dedup
        rows = sorted(set(rows))

        num_rows = len(rows)
        num_cols = len(columns)
        out = np.empty((num_rows*num_cols, 2), dtype = np.uint8)

        for i in range(num_rows):
            for j in range(num_cols):
                index = ((i) * num_cols) + j
                out[index, 0] = columns[j]
                out[index, 1] = rows[i]
        return out

    @staticmethod
    def all_8electrodes() -> np.ndarray[np.uint8]:
        """This method generates the electrode names for 96 well plates."""
        return np.array([[1, 1], [2, 1], [3, 1], [1, 2],
                         [2, 2], [1, 3], [2, 3], [3, 3]]).astype(np.uint8)

    # currently unused function
    @staticmethod
    def match_well_electrode(channelMapping:'ChannelMapping', wellElectrode:list[np.uint8]):
        """Compares a channel mapping to a list of ints representing a fully qualified electrode.
        
        Args:
            channelMapping (ChannelMapping): The channel mapping to compare.
            wellElectrode (list[int]): A list of 4 integers representing the well column, well row,
                electrode column, and electrode row of the target electrode.
        
        Returns:
            int: 1 if the channel mapping matches the target electrode, 0 otherwise."""
        if (channelMapping.well_column == wellElectrode[0]       and
            channelMapping.well_row == wellElectrode[1]          and
            channelMapping.electrode_column == wellElectrode[2]  and
            channelMapping.electrode_row == wellElectrode[3]):
            return 1
        return 0

    @staticmethod
    def get_channels_to_load(channel_array:ChannelArray,
                          target_wells:Union[list[list[int]], Literal["all"]],
                          target_els:Union[list[list[int]], Literal["all", "none"]]) \
                            -> np.ndarray[int]:
        """Parses the target wells and electrodes into a list of channels to load from the
        data array.
        
        Args:
            channel_array (ChannelArray): The channel array containing the channels
                available in the file.
            target_wells (list[list[int]] | Literal["all"]]):
                A list of [well_column, well_row] pairs specifying the wells to load,
                or "all" to load all wells.
            target_els (list[list[int]] | Literal["all"|"none"]]):
                A list of [electrode_column, electrode_row] pairs specifying the electrodes
                to load, "all" to load all electrodes, or "none" to load no electrodes.
        
        Returns:
            out (np.ndarray[int]): A 1D array of channel indices to load from the data array.
        """
        # Decode the targetWells string
        if target_wells == 'all':
            # User has requested all wells - figure out what those are from the channel array
            target_wells = DataSet.all_wells_electrodes(
                [channel.well_column for channel in channel_array.channels],
                [channel.well_row for channel in channel_array.channels])
        else:
            target_wells = np.array(target_wells)

        # Decode the targetElectrodes string
        if target_els == 'all':
            if PlateTypes.is_chimera(channel_array.plate_type):
                target_els = DataSet.all_chimera_electrodes(channel_array)
            # User has requested all electrodes - figure out what
            # those are from the channel array
            if channel_array.plate_type in [PlateTypes.NinetySixWell,
                                           PlateTypes.NinetySixWellCircuit,
                                           PlateTypes.NinetySixWellTransparent,
                                           PlateTypes.NinetySixWellLumos,
                                           PlateTypes.Reserved2]:
                target_els = DataSet.all_8electrodes()
            else:
                target_els = DataSet.all_wells_electrodes(
                    [channel.electrode_column for channel in channel_array.channels],
                    [channel.electrode_row for channel in channel_array.channels])
        elif target_els == 'none':
            # User has requested no electrodes
            target_els = np.empty((0, 2), dtype=np.uint8)
        else:
            target_els = np.array(target_els, dtype=np.uint8)

        channels_out:np.ndarray[int] = np.repeat(-1, (target_wells.shape[0]*target_els.shape[0]))
        if len(target_wells) == 0 or len(target_els) == 0:
            return channels_out.astype(int)

        # TODO: think about this some more. It can return the correct channels to load
        # but they are not in order of the requested wells or electrode but are instead
        # sorted by artichoke/artichoke channel index.
        # There is probably some way to resort them in the requested order
        # channel_map = np.array([(channel.well_column, channel.well_row,
        #                          channel.electrode_column, channel.electrode_row)
        #                        for channel in channel_array.channels])
        # well_map = np.rec.fromarrays(channel_map[:,:2].T)
        # el_map = np.rec.fromarrays(channel_map[:,2:].T)
        # out_idx = np.nonzero(np.isin(well_map, np.rec.fromarrays(target_wells.T))\
        #                      & np.isin(el_map, np.rec.fromarrays(target_els.T)))[0]
        # this shows the ordering
        # mappings = [channel_array.channels[idx] for idx in out_idx]

        
        for channel_array_index, current_channel in enumerate(channel_array.channels):
            try:
                well_idx = DataSet._ismember(
                    np.array([current_channel.well_column, current_channel.well_row]),
                    target_wells).nonzero()[0]
            # find function raises ArgumentError when dimension mismatch occurs
            # and value error when none is found
            except ValueError:
                continue

            try:
                el_idx = DataSet._ismember(
                    np.array([current_channel.electrode_column, current_channel.electrode_row]),
                    target_els).nonzero()[0]
            except ValueError:
                continue

            # check whether this actually indexes the right electrodes
            # ismember returns a 0/1 array of where the well/electrode is matched
            # also check array dimensions. They seem to be very confident
            # that the size of the _ismember arrays never mismatches
            channels_out[well_idx * target_els.shape[0] + el_idx] = channel_array_index
        
        # this shows the ordering of the matlba implementation
        # mappings_alt = [channel_array.channels[idx] for idx in channels_out if idx != -1]
        
        # Notify the user of any requested channels that weren't found in the channel array.
        # This is not necessarily an error; for example, if a whole well is requested, and
        # some channels in that well weren't recorded, we should return the well without
        # the "missing" channel.
        # in Matlab they use a zero comparison because Matlab returns 0 from ismember if it
        # is not found thus resulting in a lookup index of 0. Here I just filled the array
        # with -1 at the beginning
        missing_channels = np.nonzero(channels_out == -1)[0]
        for not_found_idx in missing_channels:
            missing_well = not_found_idx // len(target_els)
            missing_electrode = not_found_idx % len(target_els)
            print(f'Well/electrode {target_wells[missing_well]} / {target_els[missing_electrode]} '
                'not recorded in file')

        # Strip out any zeros from channel_list_out, because these correspond to channels
        # that weren't in the loaded channel array, and therefore won't be loaded.
        return channels_out[channels_out != -1].astype(int)

    @staticmethod
    def _ismember(value:np.ndarray, array_:np.ndarray, axis = 1) -> np.ndarray:
        # replicates the behaviour of matlabs ismember
        if value.shape[0] not in array_.shape:
            raise AttributeError("Find2DIndex: Value does not match array dimensions")
        tvals = array_ == value
        if len(tvals.shape) == 1:
            axis = 0
        return np.all(tvals, axis = axis).astype(int)

    def load_as_legacy_struct(self, varargin):
        """Stump method for loading legacy files. Not supported in this library."""
        # kept this as a placeholder that is not implemented
        raise NotImplementedError("Legacy formats are not supported")

    def is_raw_voltage(self):
        """Whether this dataset contains raw voltage traces."""
        if self.data_type == BlockVectorDataType.RAW_V1:
            return True
        if self.data_type == BlockVectorDataType.NAMED_CONTINUOUS_DATA:
            if self.name.casefold() == "voltage" and isinstance(self.dataset_names, list)\
            and len(self.dataset_names) == 1:
                return self.dataset_names[0].casefold() == "raw"\
                or self.dataset_names[0].casefold() == "broadband high-frequency"\
                or self.dataset_names[0].casefold() == "broadband low-frequency"
        return False

    def is_highband(self):
        """Whether this dataset contains high-band voltage traces."""
        if self.data_type == BlockVectorDataType.NAMED_CONTINUOUS_DATA:
            if self.name.casefold() == "voltage" and isinstance(self.dataset_names, list)\
            and len(self.dataset_names) == 1:
                return self.dataset_names[0].casefold() == "raw"\
                and self.dataset_names[0].casefold() == "broadband high-frequency"
        return False

    def is_lowband(self):
        """Whether this dataset contains low-band voltage traces."""
        if self.data_type == BlockVectorDataType.NAMED_CONTINUOUS_DATA:
            if self.name.casefold() == "voltage" and isinstance(self.dataset_names, list)\
            and len(self.dataset_names) == 1:
                return self.dataset_names[0].casefold() == "raw"\
                and self.dataset_names[0].casefold() == "broadband low-frequency"
        return False

    def is_raw_contractility(self):
        """Whether this dataset contains raw contractility traces."""
        if self.data_type == BlockVectorDataType.NAMED_CONTINUOUS_DATA:
            if self.name.casefold() == "impedance" and isinstance(self.dataset_names, list)\
            and len(self.dataset_names) == 1:
                return self.dataset_names[0].casefold() == "raw"
        return False

    def is_spikes(self):
        """Whether this dataset contains spike data."""
        if self.data_type == BlockVectorDataType.SPIKE_V1:
            return len(self.dataset_names) == 0\
                or (len(self.dataset_names) == 1 and self.dataset_names[0].casefold() == "spikes")
        return False

    def is_lfp(self):
        """Whether this dataset contains LFP event data."""
        if self.data_type == BlockVectorDataType.SPIKE_V1:
            return (
                len(self.dataset_names) > 0 and self.dataset_names[0].casefold() == "lfp events"
                )\
            or (len(self.dataset_names) == 1 and self.dataset_names[0].casefold() == "spikes")
        return False

    @staticmethod
    def all_chimera_electrodes(channel_array:ChannelArray) -> np.ndarray[np.uint8]:
        """Returns chimera electrode names for a given channel array"""
        chip_type = PlateTypes.get_chimera_chip_type(channel_array.plate_type)
        match chip_type:
            case PlateTypes.CreatorKitChip3DMap:
                return np.array([
                    [1, 1], [1, 2], [1, 3], [1, 4], [1, 5], [1, 6], [1, 7], [1, 8], [1, 9],
                    [2, 1], [2, 3], [2, 4], [2, 6], [2, 7], [2, 9],
                    [3, 1], [3, 2], [3, 4], [3, 6], [3, 8], [3, 9],
                    [4, 1], [4, 2], [4, 3], [4, 4], [4, 5], [4, 6], [4, 7], [4, 8], [4, 9],
                    [5, 1], [5, 4], [5, 6], [5, 9], 
                    [6, 1], [6, 2], [6, 3], [6, 4], [6, 5], [6, 6], [6, 7], [6, 8], [6, 9],
                    [7, 1], [7, 2], [7, 4], [7, 6], [7, 8], [7, 9],
                    [8, 1], [8, 3], [8, 4], [8, 6], [8, 7], [8, 9],
                    [9, 1], [9, 2], [9, 3], [9, 4], [9, 5], [9, 6], [9, 7], [9, 8], [9, 9],
                ], dtype=np.uint8)
            case PlateTypes.CreatorKitChipSpheroHD:
                    return np.array([
                        [1, 2], [1, 3], [2, 2], [2, 3], [3, 1], [3, 2], [3, 3], [3, 4],
                        [4, 1], [4, 2], [4, 3], [4, 4], [5, 2], [5, 3], [6, 2], [6, 3],
                        ])
            case _:
                return DataSet.all_wells_electrodes(
                        [c.electrode_column for c in channel_array.channels],
                        [c.electrode_row for c in channel_array.channels])
