from io import BufferedReader

import numpy as np

class ChannelMapping:
    """
    Class representing the mapping of a single readout channel on the Artichoke head stage
    to its respective well/electrode position on the plate.

    Unlike the matlab implementation, this implementation does not accept a variable number of
    arguments in the constructor, but instead defines class methods `empty` and `from_file` 
    for the vararg cases 0 and 1 respectively.
    """
    # this array conversion is done to avoid numpy deprecation warnings
    _null_byte = np.array([-1]).astype(np.uint8)[0]
    _null_word = np.array([-1]).astype(np.uint16)[0]

    def __init__(self, well_row:np.uint8, well_column:np.uint8, electrode_column:np.uint8,
                 electrode_row:np.uint8, channel_achk:np.uint8, channel_index:np.uint8,
                 aux_data:np.uint16 = _null_word) -> None:
        self.well_row = well_row
        self.well_column = well_column
        self.electrode_column = electrode_column
        self.electrode_row = electrode_row
        self.channel_achk = channel_achk
        self.channel_index = channel_index
        self.aux_data = aux_data

    def __eq__(self, __other):
        if not isinstance(__other, ChannelMapping):
            return False
        return (
            self.well_row == __other.well_row
            and self.well_column == __other.well_column
            and self.electrode_column == __other.electrode_column
            and self.electrode_row == __other.electrode_row
            and self.channel_achk == __other.channel_achk
            and self.channel_index == __other.channel_index
        )

    @classmethod
    def empty(cls):
        instance = cls.__new__(cls)
        instance.well_row = ChannelMapping._null_byte
        instance.well_column = ChannelMapping._null_byte
        instance.electrode_column = ChannelMapping._null_byte
        instance.electrode_row = ChannelMapping._null_byte
        instance.channel_achk = ChannelMapping._null_byte
        instance.channel_index = ChannelMapping._null_byte
        instance.aux_data = ChannelMapping._null_word
        return instance

    @classmethod
    def from_file(cls, file_id:BufferedReader):
        idxs = np.fromfile(file_id, dtype=np.uint8, count=6)
        aux_data = np.fromfile(file_id, dtype=np.uint16, count=1)[0]
        return cls(*idxs, aux_data)

    def __repr__(self) -> str:
        return f"ChannelMapping(W{self.well_row}{self.well_column} "\
               f"E{self.electrode_row}{self.electrode_column} " \
               f"ACHK{self.channel_achk} CHIDX{self.channel_index})"
