import warnings
from typing import TYPE_CHECKING, Iterable

import numpy as np

from ..helper_functions.load_args import LoadArgs
from ..plate_management.plate_types import PlateTypes
from ..waveforms.spike_v1 import Spike_v1
from .dataset import BlockVectorSet, DataSet

if TYPE_CHECKING:
    from ..block_vector.discontinuous_header import \
        DiscontinuousBlockVectorHeaderEntry

class SpikeDataSet(DataSet):
    def __init__(self, vector_set:'BlockVectorSet' = None,
                 discontinuous_header:'DiscontinuousBlockVectorHeaderEntry' = None):
        super().__init__(vector_set)

        n_spikes = self.num_blocks
        n_samples = self.num_datasets_per_block\
            *self.num_channels_per_block\
            *self.num_samples_per_block
        reserved_space = self.block_header_size-Spike_v1.LOADED_HEADER_SIZE
        file_name = self.source_file.file_name

        # we do not perform a type check here because we rely on pythonic duck typing
        if discontinuous_header is not None:
            self.channel_ids = discontinuous_header.channel_ids
            self.dataset_names = discontinuous_header.dataset_names
            self.duration = discontinuous_header.duration
        else:
            self.channel_ids = []
            self.dataset_names = []
            self.duration = 0

        if not (self.num_datasets_per_block == 1 and self.num_channels_per_block == 1\
        and self.num_samples_per_block >= 1 and reserved_space >= 0 and n_spikes > 0):
            self.mapped_data = np.array([])
            return

        if reserved_space == 0:
            spike_dtype = np.dtype([
                ("startingSample",       "<i8"),                # int64  (8 bytes)
                ("channel",              "u1"),                 # uint8  (1 byte)
                ("chip",                 "u1"),                 # uint8  (1 byte)
                ("triggerSample",        "<i4"),                # int32  (4 bytes)
                ("standardDeviation",    "<f8"),                # double (8 bytes)
                ("thresholdMultiplier",  "<f8"),                # double (8 bytes)
                ("data",                 "<i2", (n_samples,)),  # int16  (2*num_samples bytes)
            ], align=False)

            self.mapped_data = np.memmap(
                file_name,
                dtype=spike_dtype,
                mode="r",                           # Writable=false
                offset=int(self.data_region_start), # Offset=this.DataRegionStart (bytes)
                shape=(int(n_spikes),),             # Repeat=numSpikes
                order="C",
            )
        else:
            spike_dtype = np.dtype([
                ("startingSample",       "<i8"),                    # int64  (8 bytes)
                ("channel",              "u1"),                     # uint8  (1 byte)
                ("chip",                 "u1"),                     # uint8  (1 byte)
                ("triggerSample",        "<i4"),                    # int32  (4 bytes)
                ("standardDeviation",    "<f8"),                    # double (8 bytes)
                ("thresholdMultiplier",  "<f8"),                    # double (8 bytes)
                ("reserved",             "u1", (reserved_space,)),  # uint8  (reservedSpace bytes)
                ("data",                 "<i2", (n_samples,)),      # int16  (2*num_samples bytes)
            ], align=False)

            self.mapped_data = np.memmap(
                file_name,
                dtype=spike_dtype,
                mode="r",                           # Writable=false
                offset=int(self.data_region_start), # Offset=this.DataRegionStart
                shape=(int(n_spikes),),             # Repeat=numSpikes
                order="C",
            )
        self.load_data = self.load_spike_data

    def load_all_spikes(self):
        """
        Returns a list of electrodes and spike times for all spikes in the dataset.

        The returned electrode array has a structured dtype with fields "achk"
        (the chip number) and "channel" (the channel number).
        """
        if self.num_channels_per_block != 1:
            raise ValueError("Invalid header for SPIKE dataset: numChannelsPerBlock must be 1.")
        if self.num_datasets_per_block != 1:
            raise ValueError("Invalid header for SPIKE dataset: numDatasetsPerBlock must be 1.")
        if self.block_header_size < Spike_v1.LOADED_HEADER_SIZE:
            raise ValueError(f"Invalid header for SPIKE dataset: blockHeaderSize must "
                             f"be at least {Spike_v1.LOADED_HEADER_SIZE} bytes.")
        if self.num_samples_per_block < 1:
            raise ValueError("Invalid header for SPIKE dataset:"
                             "numSamplesPerBlock must be at least 1.")

        electrode_dtype = np.dtype([
            ("achk", "u1"),  # uint8 (1 byte)
            ("channel", "u1"),  # uint8 (1 byte)
        ])
        if self.mapped_data.size == 0:
            return np.array([], dtype=electrode_dtype), np.array([])
        data = self.mapped_data

        electrodes = np.empty(data.shape[0], dtype=electrode_dtype)
        electrodes["achk"] = data["chip"]
        electrodes["channel"] = data["channel"]
        spike_times = data["startingSample"] + data["triggerSample"]/self.sampling_frequency
        return electrodes, spike_times

    def load_spike_data(self, well=None, electrode=None,
                        timespan=None, dimension=None, subsampling_factor=1):
        load_args = LoadArgs(wells=well, electrodes=electrode, timespan=timespan,
                             dimensions=dimension, subsampling_factor=subsampling_factor)

        target_well = load_args.wells
        target_electrode = load_args.electrodes
        channels_to_load = self.get_channels_to_load(self.channel_array,
                                                     target_well, target_electrode)
        if load_args.subsampling_factor != 1:
            warnings.warn("Spike file subsampling is not supported at this time.")

        dimension = load_args.dimensions
        return self.get_spike_v1_waveforms(
            channels_to_load, load_args.timespan, dimension
        )

    def get_spike_v1_waveforms(self, channels_to_load, time_range, dimension):
        storage_type = 0
        if dimension == LoadArgs.by_well_dimensions:
            storage_type = 1
        elif dimension == LoadArgs.by_electrode_dimensions:
            storage_type = 2

        assert self.num_channels_per_block == 1, "Invalid header for SPIKE file: "\
            "incorrect channels per block"
        assert self.num_datasets_per_block == 1, "Invalid header for SPIKE file: "\
            "incorrect datasets per block"
        assert self.block_header_size >= Spike_v1.LOADED_HEADER_SIZE, \
            "Invalid header for SPIKE file: block header size too small."
        assert self.num_samples_per_block >= 1, "Invalid header for SPIKE file: "\
            "number of samples per block < 1."

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

        desired_channels_lut = np.zeros(len(self.channel_array.channels), dtype=bool)
        desired_channels_lut[channels_to_load] = True

        if self.mapped_data.size == 0:
            return np.array([])

        #TODO: Check whether we want to return the entire array or just
        # a part of the structured array
        if np.sum(desired_channels_lut) < len(self.channel_array.channels):
            loaded_spikes = self.channel_array.lookup_channel(
            self.mapped_data["chip"], self.mapped_data["channel"]
            )
            loaded_spikes = self.mapped_data[desired_channels_lut[loaded_spikes]]
        else:
            loaded_spikes = self.mapped_data

        # in python strings have the annoying property of being a subclass of iterable so checking
        # for them is not very clean. We therefore implement a check for string time ranges
        # which is not done in matlab
        if isinstance(time_range, str):
            if time_range == "all":
                # duration of spike files may not be set for older files,
                # so we take it from the data
                time_range = [0, self.mapped_data[-1]["startingSample"]+1/12500]
            else:
                raise ValueError(f"Invalid time range string: {time_range}")
        if issubclass(type(time_range), Iterable):
            time_range = tuple(time_range)
            start = time_range[0] * self.sampling_frequency
            end = time_range[1] * self.sampling_frequency
            loaded_spikes = loaded_spikes[
                (loaded_spikes["startingSample"] >= start) &
                (loaded_spikes["startingSample"] < end)
            ]
        # this implementation differs from the matlab implementation but only in the sense
        # that it replaces the arrayfun operations by a list comprehension that is performed
        # for all cases the same.

        # convert to spike objects
        loaded_spikes = [Spike_v1(
            self.channel_array.lookup_channel_mapping(spike["chip"], spike["channel"]),
            spike["startingSample"] / self.sampling_frequency,
            spike["data"],
            self,
            spike["triggerSample"],
            spike["standardDeviation"],
            spike["thresholdMultiplier"])
            for spike in loaded_spikes]

        # if we load by plate we just return a flat array
        if storage_type == 0:
            return np.array(loaded_spikes, dtype=object)
        indices = np.array([
            [
                spike.channel.well_row,
                spike.channel.well_column,
                spike.channel.electrode_column,
                spike.channel.electrode_row
            ]
            for spike in loaded_spikes]
        )
        indices -= 1 # convert to zero-based indexing
        # if by well, we group the spikes accordingly and return a 2D array
        if storage_type == 1:
            indices = indices[:,:2]
            waveforms = np.empty(max_extent[:2], dtype=object)
        # if by electrode, we return a 4D array
        elif storage_type == 2:
            waveforms = np.empty(max_extent, dtype=object)
        else:
            raise ValueError(f"Invalid storage type: {storage_type}")
        # insert the spikes into the array
        for idx, spike in zip(indices, loaded_spikes):
            if waveforms[*idx] is None:
                waveforms[*idx] = []
            waveforms[*idx].append(spike)
        return waveforms

    def load_as_legacy_struct(self, *args, **kwargs):
        """This function is not implemented as the python library does not support legacy files."""
        raise NotImplementedError("LoadAsLegacyStruct is not implemented in the python" \
        "library as legacy files are not supported.")
