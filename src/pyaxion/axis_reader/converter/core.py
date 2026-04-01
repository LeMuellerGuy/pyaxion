from pyaxion.axis_reader.block_vector.set import BlockVectorSet
from pyaxion.axis_reader.plate_management.plate_types import PlateTypes
from pyaxion.axis_reader.plate_management.channel_mapping import ChannelMapping
import numpy as np
from typing import Tuple


def GetElectrodeMappings(sourceSet: BlockVectorSet, filterAvailable: bool = True):
    """Returns a dictionary mapping the electrode indices (as they appear in the stored data)
    to the well names as the user would call them.

    Args:
        sourceSet (BlockVectorSet): The BlockVectorSet containing the data.

    Returns:
        dict[str, list[Tuple[int,int]]]: The dictionary containing well IDs (e.g. A1, B3, ...), 
            the channel names (e.g. 11, 12, 13, 14, ...) and the channel indices
            belonging to them as a list
    """
    channel_array = sourceSet.channel_array
    # request all wells
    fTargetWells = BlockVectorSet.all_wells_electrodes(
        [channel.well_column for channel in channel_array.channels],
        [channel.well_row for channel in channel_array.channels])

    # User has requested all electrodes - figure out what
    # those are from the channel array
    if channel_array.plate_type in [PlateTypes.NinetySixWell, PlateTypes.NinetySixWellCircuit,
                                   PlateTypes.NinetySixWellTransparent,
                                   PlateTypes.NinetySixWellLumos]:
        fTargetElectrodes = BlockVectorSet.all_8electrodes()
    else:
        fTargetElectrodes = BlockVectorSet.all_wells_electrodes(
            [channel.electrode_column for channel in channel_array.channels],
            [channel.electrode_row for channel in channel_array.channels])

    channelIndexList: np.ndarray[int] = np.repeat(
        -1, (fTargetWells.shape[0]*fTargetElectrodes.shape[0]))
    wellNameList = []
    channelNameList = []
    outDict: dict[str, list[Tuple[int, int]]] = {}
    if len(fTargetWells) > 0 and len(fTargetElectrodes) > 0:
        for fChannelArrayIndex, electrode in enumerate(channel_array.channels):
            try:
                # _ismember raises ArgumentError when dimension mismatch occurs
                # and value error when none is found
                fIdxWell = _ismember(np.array([electrode.well_column, electrode.well_row]),
                                     fTargetWells).nonzero()[0]
            except ValueError:
                continue

            try:
                fIdxElectrode = _ismember(
                    np.array([electrode.electrode_column,
                             electrode.electrode_row]),
                    fTargetElectrodes).nonzero()[0]
                channelNameList.append(
                    int(electrode.electrode_row*10+electrode.electrode_column))
                wellNameList.append(_channelCoordToStr(electrode))
            except ValueError:
                continue

            # check whether this actually indexes the right electrodes
            # ismember returns a 0/1 array of where the well/electrode is matched
            # also check array dimensions. They seem to be very confident
            # that the size of the _ismember arrays never mismatches
            channelIndexList[fIdxWell * fTargetElectrodes.shape[0] +
                             fIdxElectrode] = fChannelArrayIndex

        # Notify the user of any requested channels that weren't found in the channel array.
        # This is not necessarily an error; for example, if a whole well is requested, and
        # some channels in that well weren't recorded, we should return the well without
        # the "missing" channel.
        # in Matlab they use a zero comparison because Matlab returns 0 from ismember if it is not found
        # thus resulting in a lookup index of 0. Here I just filled the array with -1 at the beginning
        if filterAvailable:
            fChannelIdxZeros = np.nonzero(channelIndexList == -1)[0]
            for fIdxNotFound in fChannelIdxZeros:
                fMissingWell = fIdxNotFound // len(fTargetElectrodes)
                fMissingElectrode = fIdxNotFound % len(fTargetElectrodes)
                print(f"Well/electrode {fTargetWells[fMissingWell]} "
                      f"/{fTargetElectrodes[fMissingElectrode]} "
                      "not recorded in file")

            # Strip out any -1's from channel_list_out, because these correspond to channels that weren't in
            # the loaded channel array, and therefore won't be loaded.
            channelIndexList = channelIndexList[channelIndexList != -1].astype(
                int)

        for well_name, ch_index, ch_name in zip(wellNameList, channelIndexList, channelNameList):
            if well_name not in outDict:
                outDict[well_name] = [(ch_name, ch_index)]
            else:
                outDict[well_name].append((ch_name, ch_index))
    # make sure that the well keys are ordered and the electrodes are also ordered
    outDict = dict(sorted(outDict.items()))
    for k, v in outDict.items():
        outDict[k].sort(key=lambda t: t[0])
    return outDict


def _ismember(value: np.ndarray, array: np.ndarray, axis=1) -> np.ndarray:
    # replicates the behaviour of matlabs ismember
    if value.shape[0] not in array.shape:
        raise AttributeError(
            "Find2DIndex: Value does not match array dimensions")
    tvals = array == value
    if len(tvals.shape) == 1:
        axis = 0
    return np.all(tvals, axis=axis).astype(int)


def _channelCoordToStr(channel: ChannelMapping):
    return f"{chr(channel.well_row+64)}{channel.well_column}"
