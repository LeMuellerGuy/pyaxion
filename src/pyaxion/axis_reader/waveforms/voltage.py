from typing import TYPE_CHECKING

import numpy as np

from ..plate_management.channel_mapping import ChannelMapping
from .waveform import Waveform

if TYPE_CHECKING:
    from ..dataset.dataset import DataSet

class VoltageWaveform(Waveform):
    def __init__(self, channel:ChannelMapping, start:float, data:np.ndarray,
                 source:'DataSet', subsampleFactor:float = 1.0):
        super().__init__(channel, start, data, source, subsampleFactor)

    def get_time_voltage_vector(self):
        """Returns a time vector and a voltage vector for this waveform based
        on the raw sample data (stored as doubles) and the source header's specified voltage scale
        """
        time = self.get_time_vector()
        # original matlab:
        # I think this is because in matlab the instance itself might be an
        # array of waveforms, while in python we would have to implement
        # the same operation on a higher order class and can only
        # implement the operation for a single waveform here
        # %Get Base Data
        # fData = double([this(:).Data]);
        # fSource = [this(:).Source];
        data = self.data * self.source.voltage_scale
        return time, data

    def get_voltage_vector(self):
        """Returns a voltage vector for this waveform based
        on the raw sample data (stored as doubles) and the source header's specified voltage scale
        """
        return self.get_time_voltage_vector()[1]