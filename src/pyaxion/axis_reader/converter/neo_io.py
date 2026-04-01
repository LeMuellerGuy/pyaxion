from pyaxion.axis_reader.block_vector.set import BlockVectorSet
from pyaxion.axis_reader.plate_management.plate_types import PlateTypes
from pyaxion.axis_reader.Converter.Core import GetElectrodeMappings
from typing import Literal, Tuple
import numpy as np


def GetStreamNames(sourceSet: BlockVectorSet, order: Literal["C", "F"] = "F"):
    """Returns the names of available wells by their designation on the plate (e.g. B3, C2, ...)

    Args:
        - sourceSet (BlockVectorSet): The BlockVectorSet object containing the data. Multiple recordings in one
        file will result in multiple BlockVectorSets as far as I understand thus requiring to select a specific one.
        - order (str): Determins whether well names are returned in Fortran (column major) or C style (row major) style.

    Returns:
        - list[Tuple[str, str]]: A list of well name tuples that are unique identifiers

    Note:
        - By default the list of well names is sorted in column major (Fortran) style, e.g. A1, A2, ..., B1, B2, ...
    """
    fMaxExtents = PlateTypes.get_electrode_dimensions(
        sourceSet.channel_array.plate_type)
    if len(fMaxExtents) == 0:  # check for failed recognition which results in 0 length tuple
        fMaxExtents = \
            (
                max([ch.well_row for ch in sourceSet.channel_array.channels]),
                max([ch.well_column for ch in sourceSet.channel_array.channels]),
                max([ch.electrode_column for ch in sourceSet.channel_array.channels]),
                max([ch.electrode_column for ch in sourceSet.channel_array.channels])
            )
    # sort Well names in C style (row major) order
    if order.casefold() == "c".casefold():
        def key_fun(well): return well[0]*fMaxExtents[0]+well[1]
    # sort well names in Fortran style (column major) order
    else:
        def key_fun(well): return well[0]+well[1]*fMaxExtents[1]

    # returns a (column major flat iter) sorted list of unique wells with their respective coordinates
    availableChannels = sorted(set([(ch.well_row, ch.well_column)
                               for ch in sourceSet.channel_array.channels]), key=key_fun)

    streamNames: list[str] = []
    for channel in availableChannels:
        # chose to not obfuscate the names of the wells because that
        # only causes the user to enter eronious well names that have
        # to be sanitized
        # e.g. for i = 7 -> A7
        # +64 is for ASCII capital letters
        streamNames.append(f"{chr(channel[0]+64)}{channel[1]}")
    return streamNames


def GetUVGain(sourceSet: BlockVectorSet):
    """Returns the gain in µV.

    Args:
        sourceSet (BlockVectorSet): The BlockVectorSet containing the data.

    Returns:
        float: The gain in µV.
    """
    return float(sourceSet.header.voltage_scale * 1e6)


def MapDataMemory(sourceSet: BlockVectorSet):
    """Returns a memory map to the BlockVectorData contained in sourceSet.

    Args:
        sourceSet (BlockVectorSet): The target BlockVectorSet.

    Returns:
        np.memmap[int16]: A numpy memmap object to the data in the file. Shape: n_timepoints, n_channels
    """
    fSampleFreq = int(sourceSet.header.sampling_frequency)
    fChannelCount = int(sourceSet.header.num_channels_per_block)
    fBytesPerSecond = fSampleFreq * fChannelCount * 2
    fNumSamples = float(sourceSet.data.entry_record.length) / \
        float(fBytesPerSecond) * fSampleFreq
    nChannels = len(sourceSet.channel_array.channels)
    return np.memmap(sourceSet.source_file.FileID, dtype=np.int16, mode="r",
                     offset=sourceSet.data.start, shape=(int(fNumSamples), nChannels), order="C")

def GetChannelMappings(sourceSet: BlockVectorSet):
    return GetElectrodeMappings(sourceSet, filterAvailable=True)