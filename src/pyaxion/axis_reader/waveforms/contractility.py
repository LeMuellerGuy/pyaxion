from typing import TYPE_CHECKING

import numpy as np

from ..plate_management.channel_mapping import ChannelMapping
from .waveform import Waveform

if TYPE_CHECKING:
    from ..dataset.dataset import DataSet

class ContractilityWaveform(Waveform):
    def __init__(self, channel:ChannelMapping, start:float, data:np.ndarray,
                 source:'DataSet', subsampleFactor:float = 1.0):
        super().__init__(channel, start, data, source, subsampleFactor)

    def get_time_contractility_vector(self):
        """Returns a time vector and a contractility vector for this waveform based
        on the raw sample data (stored as doubles) in percentage change from baseline
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
        # fVoltageScale = [fSource(:).VoltageScale];
        # contractilityData = fData * diag(fVoltageScale);
        voltage_scale = self.source.header.voltage_scale
        data = self.data * voltage_scale
        baseline = np.polynomial.Polynomial.fit(time, data, 1)(time)
        data = (data-baseline)*100/baseline
        return time, data

    def get_contractility_vector(self):
        """Returns a contractility vector for this waveform based
        on the raw sample data (stored as doubles) in percentage change from baseline
        """
        return self.get_time_contractility_vector()[1]

    def get_time_impedance_vector(self):
        """Returns a time vector and an impedance vector for this waveform based
        on the raw sample data (stored as doubles) and the source
        header's specified voltage scale"""
        time = self.get_time_vector()
        voltage_scale = self.source.header.voltage_scale
        data = self.data * voltage_scale
        return time, data

    def get_impedance_vector(self):
        """Returns an impedance vector for this waveform based
        on the raw sample data (stored as doubles) and the source
        header's specified voltage scale"""
        return self.get_time_impedance_vector()[1]
