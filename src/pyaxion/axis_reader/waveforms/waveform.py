import numpy as np

from ..dataset.dataset import DataSet
from ..plate_management.channel_mapping import ChannelMapping


class Waveform:
    def __init__(self, channel:ChannelMapping, start:float,
                 data:np.ndarray, source:'DataSet', subsample_factor:float = 1.0):

        if channel is None:
            return

        if not isinstance(channel, ChannelMapping):
            raise ValueError(f'Waveform: Unexpected Argument for aChannel: {channel}')

        if not isinstance(source, DataSet):
            raise ValueError(f'Waveform: Unexpected Argument for aSource: {source}')

        self.channel = channel
        self.start = start
        self.data = data
        self.source = source
        self.subsample_factor = subsample_factor

    @classmethod
    def empty(cls):
        out = cls.__new__(cls)
        out.channel = None
        out.start = 0
        out.data = np.array([])
        out.source = None
        out.subsample_factor = 1.0
        return out

    # these functions do not have the same array operation
    # functionality of the orginal due to the different
    # coding style in python
    def get_time_voltage_vector(self):
        time_data = self.get_time_vector()
        voltage_data = self.get_voltage_vector()
        return time_data, voltage_data
    
    def get_voltage_vector(self):
        return self.data * self.source.voltage_scale
    
    def get_time_vector(self):
        sampling_frequency = 1. / self.source.sampling_frequency

        num_samples = self.data.shape[0]
        time_data = np.arange(num_samples)
        time_data = time_data * self.subsample_factor
        time_data = time_data * sampling_frequency

        time_data = time_data + self.start
        return time_data
