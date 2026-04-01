import numpy as np

from ..helper_functions.led_color import LedColor

class LedPosition:
    """
    CHANNELMAPPING represents the Position and color of an LED on an optical stimulation device.
    """
    # creates a signed integer and reinterprets the bits
    # as a unsigned integer which may not be the same
    # as just creating an unsigned integer in the first place
    # the .copy is more of a safety thing because views can be
    # altered in memory
    nullByte = np.uint8(0)

    def __init__(self, *args):
        n_args = len(args)

        if n_args == 0:
            # Create a nonsense (Null) Channel Mapping
            self.well_row = LedPosition.nullByte
            self.well_column = LedPosition.nullByte
            self.led_color = LedColor.NONE

        elif n_args == 1:
            # Assume Argument is a numpy.fromfile or file ID from fOpen and that is
            # seeked to the correct spot, read in arguments from this file
            a_file_id = args[0]

            self.well_column:np.uint8 = np.fromfile(a_file_id, dtype=np.uint8, count=1)[0]
            self.well_row:np.uint8 = np.fromfile(a_file_id, dtype=np.uint8, count=1)[0]
            self.led_color = LedColor(np.fromfile(a_file_id, dtype=np.uint16, count=1)[0])

        elif n_args == 3:
            # Construct a new Channel Mapping from Scratch
            # Argument order is(WellRow, WellColumn, ElectrodeColumn, ElectrodeRow,
            # ChannelAchk, ChannelIndex)
            self.well_row = np.uint8(args[0])
            self.well_column = np.uint8(args[1])
            self.led_color = LedColor(np.uint16(args[2]))
        else:
            raise ValueError('Argument Error')

    def __eq__(self, __other):
        if not isinstance(__other, LedPosition):
            return False
        return (self.well_row == __other.well_row and
                self.well_column == __other.well_column and
                self.led_color == __other.led_color)
