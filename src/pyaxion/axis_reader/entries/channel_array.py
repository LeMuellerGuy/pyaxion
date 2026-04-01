from ctypes import c_uint32
from io import BufferedReader
from typing import TYPE_CHECKING

import numpy as np

from ..plate_management.channel_mapping import ChannelMapping
from .entry import Entry
from .entry_record import EntryRecord

if TYPE_CHECKING:
    from ..helper_functions.group_structs import ChannelID


class ChannelArray(Entry):
    """
    Class that represents a list of loaded Channels in a BlockVectorDataSet.
    """
    @property
    def plate_type(self):
        return self.basic_channel_array.plate_type

    @property
    def channels(self):
        return self.basic_channel_array.channels

    def __init__(self, entry_record:EntryRecord = None, file_id:BufferedReader = None):
        super().__init__(entry_record, np.int64(file_id.tell()) if file_id is not None else None)
        if file_id is None:
            self.basic_channel_array = BasicChannelArray()
        else:
            start = file_id.tell()
            self.basic_channel_array = BasicChannelArray.from_file(file_id)
            assert self.entry_record.length == np.int64(file_id.tell()) - start, \
                f"Unexpected ChannelArray length in {file_id.name}"

    # in the newer version of the matlab code, axion decided to wrap most of the functionality
    # and move everything to the `BasicChannelArray` class.
    def lookup_channel_id(self, channelID:'ChannelID'):
        return self.basic_channel_array.lookup_channel_id(channelID)

    def lookup_electrode(self, well_column:int, well_row:int,
                         electrode_column:int, electrode_row:int):
        return self.basic_channel_array.lookup_electrode(well_column, well_row,
                                                        electrode_column, electrode_row)

    def lookup_channel(self, channel_achk:int, channel_index:int):
        return self.basic_channel_array.lookup_channel(channel_achk, channel_index)

    def lookup_channel_mapping(self, channel_achk:int, channel_index:int):
        return self.basic_channel_array.lookup_channel_mapping(channel_achk, channel_index)

    def get_new_for_channels(self, channels:list[ChannelMapping]):
        new = ChannelArray()
        new.basic_channel_array = BasicChannelArray(
            plate_type=self.plate_type,
            channels=channels
        )
        return new

class BasicChannelArray:
    def __init__(self, plate_type:int = None, channels:list[ChannelMapping] = None):
        self.plate_type = plate_type if plate_type is not None else 0
        self.channels:list[ChannelMapping] = channels if channels is not None else []
        self.electrode_lut:dict[np.int32, np.int32] = {}
        self.channel_lut:dict[np.int32, np.int32] = {}
        self._rebuild_hash_maps()

    @classmethod
    def from_file(cls, file_id:BufferedReader):
        plate_type = int.from_bytes(file_id.read(4), 'little', signed=False)
        n_channels = int.from_bytes(file_id.read(4), 'little', signed=False)
        channels = [ChannelMapping.from_file(file_id) for _ in range(n_channels)]
        return cls(plate_type, channels)

    def _rebuild_hash_maps(self):
        self.electrode_lut:dict[np.int32, np.int32] = {}
        # because matlab allows overflowing indices to just expand the array this has
        # to be tackled differently and the array must be as long as the maximum expected
        # channel hash it is actually not entirely clear to me why they chose to use an array
        # as a substitute for an actual hash structure here but did use a hash map for the
        # electrodes

        self.channel_lut:dict[np.int32, np.int32] = {}
        for index, channel in enumerate(self.channels):
            el_hash, ch_hash = BasicChannelArray._hash_channel_mapping(channel)

            # I don't know why they raise an error here, it shouldn't matter
            if el_hash in self.electrode_lut:
                raise ValueError('Key already added')

            self.electrode_lut[el_hash] = index
            # since we are using a dict, the indexing is not that relevant
            self.channel_lut[ch_hash] = index

    @staticmethod
    def _hash_channel_mapping(channel_mapping:ChannelMapping):
        return (BasicChannelArray._hash_el(channel_mapping.well_column,
                                                 channel_mapping.well_row,
                                                 channel_mapping.electrode_column,
                                                 channel_mapping.electrode_row),
                BasicChannelArray._hash_ch(channel_mapping.channel_achk,
                                               channel_mapping.channel_index))

    @staticmethod
    def _hash_el(well_column:int, well_row:int, electrode_column:int, electrode_row:int):
        h = c_uint32(c_uint32(well_column).value << 24)
        h = c_uint32(c_uint32(well_row).value << 16 | h.value)
        h = c_uint32(c_uint32(electrode_column).value << 8 | h.value)
        h = c_uint32(c_uint32(electrode_row).value | h.value)
        return np.uint32(h)

    @staticmethod
    def _hash_ch(channel_achk:int, channel_index:int):
        h = c_uint32(c_uint32(channel_achk).value << 8)
        h = c_uint32(channel_index).value | h.value
        return np.uint32(h)

    def lookup_electrode(self, well_column:int, well_row:int,
                         electrode_column:int, electrode_row:int):
        electrode_hash = BasicChannelArray._hash_el(well_column, well_row,
                                                   electrode_column, electrode_row)
        return self.electrode_lut[electrode_hash]

    def lookup_channel(self, channel_achk:int, channel_index:int):
        channel_hash = BasicChannelArray._hash_ch(channel_achk, channel_index)
        return self.channel_lut[channel_hash]

    def lookup_channel_mapping(self, channel_achk:int, channel_index:int):
        return self.channels[self.lookup_channel(channel_achk, channel_index)]

    def lookup_channel_id(self, channelID:'ChannelID'):
        return self.lookup_channel(channelID.artichoke, channelID.channel)
