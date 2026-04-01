from copy import copy
from typing import TYPE_CHECKING
from enum import IntEnum

import pyaxion.axis_reader.block_vector.data as BlockData

from ..entries.channel_array import ChannelArray
from .header import BlockVectorHeader
from .header_extension import BlockVectorHeaderExtension
from .combined_header import CombinedBlockVectorHeaderEntry

if TYPE_CHECKING:
    from ..axis_file import AxisFile

class ReturnDimension(IntEnum):
    """Enum defining available return dimensions for the data in a BlockVectorSet."""
    BYPLATE = 1
    BYWELL = 3
    BYELECTRODE = 5
    DEFAULT = 0


class BlockVectorSet:
    """
    BlockVectorSet is a grouping of data and metadata for a series of data
    contained within an AxisFile. This class is composed of 4 major parts:

    - ChannelArray: The channel array (See ChannelArray.py) is a listing of 
        all of the channels that were recorded in this loaded set.

    - Header: The header of the data (See BlockVectorHeader.py) contains the basic infomation
        that is used in loading and using the data in this set (e.g. Sampling Frequency,
        Voltage Scale, etc...)

    - HeaderExtension: The header extension (See BlockVectorHeaderExtension.py)
        contains metadata about the data capture / Reprocessing.

    - Data: The data in this file (See `data.py`) contains the methods for
        loading the sample data from this set.
    """
    def __init__(self, *args):
        self.source_file:'AxisFile' = None
        self.channel_array:ChannelArray = None
        self.header:BlockVectorHeader = None
        self.header_extension:BlockVectorHeaderExtension = None
        self.data:BlockData.BlockVectorData = None
        self.combined_block_vector:CombinedBlockVectorHeaderEntry = None
        self.set_values(*args)

    @property
    def handle(self):
        """Alias for source_file, returning the AxisFile instance."""
        return self.source_file

    def clone(self, *args):
        """Deprecated and disfunctional method that was intended to copy the current
        object. Known issues: Does not copy the attributes and creates an empty copy instead"""
        clone = BlockVectorSet()
        clone.set_values(*args)
        return clone

    def set_values(self, *args):
        """Sets the attributes of the current object based on the arguments' types.
        
        It might be deprecated in the future in favor of a more explicit constructor."""
        from ..axis_file import AxisFile # pylint: disable=import-outside-toplevel
        for arg in args:
            if isinstance(arg, ChannelArray):
                self.channel_array = arg
            elif isinstance(arg, BlockVectorHeader):
                self.header = arg
            elif isinstance(arg, BlockVectorHeaderExtension):
                self.header_extension = arg
            elif isinstance(arg, BlockData.BlockVectorData):
                self.data = arg
            elif isinstance(arg, AxisFile):
                self.source_file = arg
            elif isinstance(arg, CombinedBlockVectorHeaderEntry):
                self.combined_block_vector = arg
                self.header = arg
                self.header_extension = arg
            else:
                raise ValueError('Unknown member type')

    def __deepcopy__(self, memo=None):
        # Create a new instance of BlockVectorSet
        new_instance = BlockVectorSet()

        # Copy the attributes to the new instance
        new_instance.source_file = self.source_file
        new_instance.channel_array = copy(self.channel_array)
        new_instance.header = copy(self.header)
        new_instance.header_extension = copy(self.header_extension)
        new_instance.data = copy(self.data)

        return new_instance
