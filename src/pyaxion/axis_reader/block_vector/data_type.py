import warnings
from enum import IntEnum


class BlockVectorDataType(IntEnum):
    """Enumerates the available data types for the data in a BlockVectorSet."""
    RAW_V1 = 0
    SPIKE_V1 = 1
    NAMED_CONTINUOUS_DATA = 2
    @staticmethod
    def try_parse(value:int):
        try:
            value = BlockVectorDataType(value)
            success = True
        except ValueError as e:
            warnings.warn(f"BlockVectorDataType: Unsupported BlockVectorDataType {value}, "
                  f"failed with error {e}")
            success = False
        return (value, success)
