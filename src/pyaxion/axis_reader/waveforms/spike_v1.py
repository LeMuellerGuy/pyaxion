from typing import TYPE_CHECKING

import numpy as np

from ..plate_management.channel_mapping import ChannelMapping
from ..waveforms.waveform import Waveform

if TYPE_CHECKING:
    from ..dataset.dataset import DataSet


#from pyaxion.AxisReader.BlockVector.BlockVectorSet import BlockVectorSet

class Spike_v1(Waveform):
    """
    SPIKE_V1: An extension of Waveform that represents a spike recorded by
              spike detector in Axis.
    
    TriggerSampleOffset: Offset (in samples) from the start of the
                         waveform where the spike detector was
                         triggered

    StandardDeviation:   RMS voltage value of the signal noise at the
                         time the spike was caputred

    ThresholdMultiplier: Multiplier(if applicable) of the RMS Noise that was 
                         used as the trigger voltage for this spike
    
    """

    LOADED_HEADER_SIZE = 30
    # possibly adjust the type hints and create appropriate properties
    def __init__(self, channel:ChannelMapping, start:float, data:np.ndarray, source:'DataSet',
                 triggerSampleOffset:int, standardDeviation:int, thresholdMultiplier:int):
        super().__init__(channel, start, data, source, 1)
        self.trigger_sample_offset = triggerSampleOffset
        self.standard_deviation = standardDeviation
        self.threshold_multiplier = thresholdMultiplier
        # We do not support spike data subsampling at this time.
        # so it is always set to 1
