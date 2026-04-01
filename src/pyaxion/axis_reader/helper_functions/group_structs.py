from io import BufferedReader

import numpy as np

from ..plate_management.channel_mapping import ChannelMapping
from ..plate_management.led_position import LedPosition


class ChannelGroup:
    """
    Class containing information about channels.
    
    Fields:
        - ID: Channel Id
        - PlateType: The plate type that the channel is contained in
        - Mappings: Channel coordinates"""
    def __init__(self, id_:np.uint32, plate_type:np.uint32, mappings:ChannelMapping) -> None:
        self.id = id_
        self.plate_type = plate_type
        self.mappings = mappings

class LedGroup:
    """
    Class containing information about Leds.
    
    Fields:
        - ID: Led Id
        - PlateType: The plate type that the LED is contained in
        - Mappings: LED coordinates"""
    def __init__(self, id_:np.uint32, plate_type:np.uint32, mappings:list[LedPosition]) -> None:
        self.id = id_
        self.plate_type = plate_type
        self.mappings = mappings

class Electrodes:
    """Class that holds two arrays of information about electrode routing to
    the Artichoke head stage and the respective channels.
    """
    def __init__(self, achk:np.ndarray[np.int8], channel:np.ndarray[np.int8]) -> None:
        self.artichoke = achk
        self.channel = channel

class ChannelID:
    """Class introduced in version 1.3 that replaces the Electrodes class.
    It is generated in the same way except that the np.int8 arrays are read in as a single
    int16 and then bitshifted to extract the information. We keep this duality for consistency
    with the matlab implementation."""
    def __init__(self, guid:np.uint16):
        self.channel = guid & 0x00FF
        self.artichoke = (guid & 0xFF00) >> 8

    @classmethod
    def from_file(cls, file_id:BufferedReader):
        return cls(np.fromfile(file_id, dtype=np.uint16, count=1)[0])

    def __repr__(self) -> str:
        return f"ChannelID(ACHK{self.artichoke} CHIDX{self.channel})"
