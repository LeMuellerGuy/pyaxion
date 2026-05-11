import mmap
import warnings
from typing import TYPE_CHECKING, Iterable

import numpy as np

from ..block_vector.sample_type import BlockVectorSampleType
from ..block_vector.set import ReturnDimension
from ..block_vector.continuous_header import \
    ContinuousBlockVectorHeaderEntry
from ..helper_functions.load_args import LoadArgs
from ..plate_management.plate_types import PlateTypes
from ..waveforms.contractility import ContractilityWaveform
from ..waveforms.voltage import VoltageWaveform
from ..waveforms.waveform import Waveform
from .dataset import BlockVectorSet, DataSet

if TYPE_CHECKING:
    from ..entries.channel_array import ChannelArray, ChannelMapping

class ContinuousDataSet(DataSet):
    """Dataset subclass for continuous waveform data, e.g. raw voltage traces."""
    def __init__(self, vector_set:BlockVectorSet,
                 header_entry:ContinuousBlockVectorHeaderEntry = None) -> None:
        super().__init__(vector_set)
        self.load_data = self.load_raw_data
        if header_entry is None:
            self.dataset_names = []
            self.duration = 0
        else:
            channel_array:ChannelArray = self.channel_array # pylint: disable=access-member-before-definition
            self.dataset_names = header_entry.dataset_names
            self.channel_array:ChannelArray = self.channel_array.get_new_for_channels(
                [channel_array.channels[channel_array.lookup_channel_id(id_)]
                 for id_ in header_entry.channel_ids]
            )
            if header_entry.duration is None:
                self.duration = self.data_region_length/(self.sampling_frequency*self.num_blocks)
            else:
                self.duration = header_entry.duration

    def get_continuous_waveform(self, channels_to_load:Iterable[int],
                                timespan:Iterable[int]|None = None,
                                dimension:ReturnDimension = ReturnDimension.DEFAULT,
                                subsampling_factor:int = 1):
        """Loads the raw data for the specified channels in the given time span:
        
        Args:
            channels_to_load (Iterable[int]): An iterable of channel indices to load.
            timespan (Iterable[int], optional): A tuple of (start, end) time in seconds to load.
                If None, all time points will be loaded. Defaults to None.
            dimension (ReturnDimension, optional): The dimension in which to return the data.
                Defaults to ReturnDimension.DEFAULT.
            subsampling_factor (int, optional): The factor by which to subsample the data.
                Defaults to 1 (no subsampling).
        
        Returns:
            out (np.ndarray[Waveform]): An array of waveform objects. The shape is determined
                by the dimension argument:
                - ReturnDimension.BYPLATE: A 1D array of waveforms.
                - ReturnDimension.BYWELL: A 2D array of waveforms with shape
                    (n_wells_row, n_wells_column).
                - ReturnDimension.BYELECTRODE: A 4D array of waveforms with shape
                    (n_wells_row, n_wells_column, n_electrode_columns, n_electrode_rows).
            The objects may be subclasses of Waveform (e.g. VoltageWaveform, ContractilityWaveform).
        """
        sample_size = BlockVectorSampleType.get_size_in_bytes(self.sample_type)
        read_precision = BlockVectorSampleType.get_read_precision(self.sample_type)

        self.file_id.seek(self.data_region_start)
        start = 0

        bytes_per_second = self.sampling_frequency*self.num_channels_per_block*sample_size
        max_time = self.data_region_length/bytes_per_second

        if timespan != "all":
            start, end = timespan
            assert start < end, f"Invalid timespan: {timespan}. "\
                +"Must be increasing."
            start = max(0, start)

            skip_initial_samples = int(start*self.sampling_frequency)
            # cast to int to prevent overflow for large offsets
            skip_initial_bytes = skip_initial_samples*int(self.num_channels_per_block)*sample_size

            if start > max_time:
                warnings.warn(f"Start time {start} exceeds maximum time {max_time}. "
                              f" Returning empty array.")
                return Waveform.empty()

            if end > max_time:
                warnings.warn(f"End time {end} exceeds maximum time {max_time}."
                              f" Adjusting end time to {max_time}.")
                end = max_time

            num_samples = int((end - start)*self.sampling_frequency)
            self.file_id.seek(skip_initial_bytes, 1)
        else:
            num_samples = int(max_time*self.sampling_frequency)

        n_channels = len(self.channel_array.channels)
        max_extent = PlateTypes.get_electrode_dimensions(self.channel_array.plate_type)

        if len(max_extent) == 0:
            channels = self.channel_array.channels
            max_extent = np.array(
                [
                    max(c.well_row for c in channels),
                    max(c.well_column for c in channels),
                    max(c.electrode_column for c in channels),
                    max(c.electrode_row for c in channels)
                ]
            )

        if dimension == ReturnDimension.BYWELL:
            # check whether a specific dtype is necessary here
            waveforms:np.ndarray[Waveform] = np.empty((max_extent[0], max_extent[1]),
                                                      dtype = Waveform)
        elif dimension == ReturnDimension.BYELECTRODE:
            waveforms:np.ndarray[Waveform] = np.empty(max_extent, dtype = Waveform)
        else:
            # using a list here is more efficient since numpy's append
            # always has to create a new copy
            waveforms:np.ndarray[Waveform] = []

        if len(channels_to_load) == 1:
            # equivalent matlab line:
            # fread(this.FileID, aChannelsToLoad - 1, ['1*' fFreadPrecision]);
            self.file_id.seek(channels_to_load[0]*read_precision().nbytes, 1)
            # we use a memmap to mimic the skip behaviour of matlab fread
            # using numpy memmap doesn't allow us to specify the strides, so we read
            # directly from a buffer and copy the data to avoid segfault when the mmmap is closed

            # TODO: check whether the strides need to be multiplied by the byte size of the sample
            # type or whether numpy infers this from the dtype
            num_samples = num_samples*subsampling_factor*n_channels
            data = np.memmap(self.file_id, dtype=read_precision, mode='r',
                             offset=self.file_id.tell(), shape=(num_samples,))
            # stride out the other channels
            data = data[:num_samples:n_channels]
            # subsample the data
            data = data[:num_samples:subsampling_factor]
            mapping:ChannelMapping = self.channel_array.channels[channels_to_load[0]]
            if self.is_raw_voltage():
                temp_wave = VoltageWaveform(mapping, start, data, self, subsampling_factor)
            elif self.is_raw_contractility():
                temp_wave = ContractilityWaveform(mapping, start, data, self, subsampling_factor)
            else:
                temp_wave = Waveform(mapping, start, data, self, subsampling_factor)

            out_index = np.array([mapping.well_row, mapping.well_column,
                                  mapping.electrode_column, mapping.electrode_row])

            if dimension == ReturnDimension.BYPLATE:
                waveforms.append(temp_wave)
            elif dimension == ReturnDimension.BYWELL:
                waveforms[out_index[0], out_index[1]] = temp_wave
            elif dimension == ReturnDimension.BYELECTRODE:
                waveforms[tuple(out_index)] = temp_wave
            else:
                raise ValueError(f"Invalid dimension: {dimension}")
            return np.array(waveforms, dtype=Waveform)

        # case more channels to load
        num_samples = num_samples//subsampling_factor*n_channels
        # unfortunately, replicating matlab's fread striding behaviour is not straightforward in
        # python. We could manually seek and read but this would be much slower than just
        # reading everything and then indexing into it.
        # We could also consider creating a custom dtype on the fly and then using strided indexing
        # to avoid reading all the data
        data = np.memmap(self.file_id, dtype=read_precision, mode='r', offset=self.file_id.tell(),
                         shape=(num_samples*subsampling_factor,))
        data = data[:num_samples:subsampling_factor]
        if len(data) % n_channels != 0:
            warnings.warn(f"Number of samples {len(data)} is not a multiple of number of"
                          f"channels {n_channels}. This may indicate an issue with the"
                           "data or the specified time range.")
            num_samples = (len(data)//n_channels)*n_channels
            data = data[:num_samples]
        data = data.reshape(n_channels, -1, order = "F")

        if dimension == ReturnDimension.DEFAULT:
                dimension = ReturnDimension.BYPLATE

        for channel in channels_to_load:
            mapping:ChannelMapping = self.channel_array.channels[channel]
            channel_data = data[channel, :]
            if self.is_raw_voltage():
                temp_wave = VoltageWaveform(mapping, start, channel_data,
                                            self, subsampling_factor)
            elif self.is_raw_contractility():
                temp_wave = ContractilityWaveform(mapping, start, channel_data,
                                                    self, subsampling_factor)
            else:
                temp_wave = Waveform(mapping, start, channel_data,
                                        self, subsampling_factor)

            if dimension == ReturnDimension.BYPLATE:
                waveforms.append(temp_wave)
                continue
            out_index = np.array([mapping.well_row, mapping.well_column,
                                    mapping.electrode_column, mapping.electrode_row])
            out_index -= 1
            if dimension == ReturnDimension.BYWELL:
                waveforms[out_index[0], out_index[1]] = temp_wave
            elif dimension == ReturnDimension.BYELECTRODE:
                waveforms[tuple(out_index)] = temp_wave
            else:
                raise ValueError(f"Invalid dimension: {dimension}")
        return np.array(waveforms, dtype=Waveform)

    def load_raw_data(self, wells:str|None=None, electrode:str|None=None,
                      timespan:Iterable[int]|None = None,
                      dimension:ReturnDimension = ReturnDimension.DEFAULT,
                      subsampling_factor:int = 1):
        """Loads the raw data for the specified wells and electrodes in the given time range.
        
        Args:
            wells (str, optional): A comma delimited string of wells to load (e.g. "A1,B2") or None.
                If None, all wells will be loaded. Defaults to None.
            electrodes (str, optional): A comma delimited string of electrodes to load
                (e.g. "11,12") or None. If None, all electrodes will be loaded.
                Defaults to None.
            timespan (Iterable[int], optional): A tuple of (start, end) time in seconds to load.
                If None, all time points will be loaded. Defaults to None.
            dimension (ReturnDimension, optional): The dimension in which to return the data.
                Defaults to ReturnDimension.DEFAULT.
            subsampling_factor (int, optional): The factor by which to subsample the data.
                Defaults to 1 (no subsampling).
        
        Returns:
            out (np.ndarray[Waveform]): An array of waveform objects. The shape is determined
                by the dimension argument:
                - ReturnDimension.BYPLATE: A 1D array of waveforms.
                - ReturnDimension.BYWELL: A 2D array of waveforms with shape
                    (n_wells_row, n_wells_column).
                - ReturnDimension.BYELECTRODE: A 4D array of waveforms with shape
                    (n_wells_row, n_wells_column, n_electrode_columns, n_electrode_rows).
        The objects may be subclasses of Waveform (e.g. VoltageWaveform,
        ContractilityWaveform) depending on the type of data in the dataset.
        """
        load_args = LoadArgs(wells, electrode, timespan, dimension,
                             subsampling_factor=subsampling_factor)
        channels_to_load = DataSet.get_channels_to_load(self.channel_array,
                                                     load_args.wells,
                                                     load_args.electrodes)
        dimension = load_args.dimensions
        subsampling_factor = load_args.subsampling_factor
        return self.get_continuous_waveform(
            channels_to_load=channels_to_load,
            timespan=load_args.timespan,
            dimension=dimension,
            subsampling_factor=subsampling_factor
        )

    def load_as_legacy_struct(self, *args, **kwargs):
        """This function is not implemented as the python library does not support legacy files."""
        raise NotImplementedError("LoadAsLegacyStruct is not implemented in the python" \
        "library as legacy files are not supported.")
