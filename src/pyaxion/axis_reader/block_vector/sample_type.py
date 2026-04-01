from enum import Enum
import warnings

import numpy as np

class BlockVectorSampleType(Enum):
    """Enum defining possible sample data types for a block vector's data."""
    INT16 = 0
    INT32 = 1
    FLOAT32 = 2
    FLOAT64 = 3

    @staticmethod
    def try_parse(value:int):
        """Tries to parse an integer value as a BlockVectorSampleType.
        
        Does not raise errors but instead returns a second value indicating parsing success."""
        try:
            return BlockVectorSampleType(value), True
        except ValueError:
            warnings.warn(f"Unsupported sample type: {value}")
            return value, False

    @staticmethod
    def get_size_in_bytes(value:'int|BlockVectorSampleType'):
        """Returns the size in bytes of a given sample type."""
        try:
            value = BlockVectorSampleType(value)
        except ValueError as e:
            raise ValueError(f"Unsupported sample type: {value}") from e
        if value == BlockVectorSampleType.INT16:
            return 2
        if value == BlockVectorSampleType.INT32:
            return 4
        if value == BlockVectorSampleType.FLOAT32:
            return 4
        if value == BlockVectorSampleType.FLOAT64:
            return 8

    @staticmethod
    def get_read_precision(value:'int|BlockVectorSampleType'):
        """Returns the numpy dtype to use when reading data of the given sample type."""
        try:
            value = BlockVectorSampleType(value)
        except ValueError as e:
            raise ValueError(f"Unsupported sample type: {value}") from e
        if value == BlockVectorSampleType.INT16:
            return np.int16
        if value == BlockVectorSampleType.INT32:
            return np.int32
        if value == BlockVectorSampleType.FLOAT32:
            return np.float32
        if value == BlockVectorSampleType.FLOAT64:
            return np.float64
