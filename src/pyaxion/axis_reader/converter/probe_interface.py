from pyaxion.axis_reader.block_vector.set import BlockVectorSet
from pyaxion.axis_reader.plate_management.plate_types import PlateTypes
from pyaxion.axis_reader.Converter.Core import GetElectrodeMappings
from enum import Enum
from typing import Self, SupportsFloat, Union
from math import sqrt


class Point(object):
    """Class that represents a 2D Point.
    """
    @property
    def XInv(self):
        """Point mirrored along the Y-Axis (x value inverted)."""
        return Point(-self.X, self.Y)

    @property
    def YInv(self):
        """Point mirrored along the X-Axis (y value inverted)."""
        return Point(self.X, -self.Y)

    def __init__(self, x: Union[float, int], y: Union[float, int]) -> None:
        """Class that represents a 2D Point.

        Args:
            x (float | int): The x coordinate.
            y (float | int): The y coordinate.
        """
        self.X = x
        self.Y = y

    def __add__(self, __other: Union[Self, SupportsFloat]):
        if not issubclass(type(__other), SupportsFloat) and not isinstance(self, Point):
            raise ValueError("Objects cannot be added")
        if isinstance(__other, Point):
            return Point(self.X + __other.X, self.Y + __other.Y)
        else:
            return Point(self.X + __other, self.Y + __other)

    def __sub__(self, __other: Union[Self, SupportsFloat]):
        if not issubclass(type(__other), SupportsFloat) and not isinstance(self, Point):
            raise ValueError("Objects cannot be subtracted")
        if isinstance(__other, Point):
            return Point(self.X - __other.X, self.Y - __other.Y)
        else:
            return Point(self.X - __other, self.Y - __other)

    def __iter__(self):
        for val in (self.X, self.Y):
            yield val

    def __neg__(self):
        return Point(-self.X, -self.Y)


class Electrode:
    """Class that holds information about the position and indexing of an electrode on an Axion MEA plate.
    """

    def __init__(self, id: int, relPos: Point, absPos: Point, channel: int, radius:float) -> None:
        self.RelPos = relPos
        """Position relative to the well center."""
        self.AbsPos = absPos
        """Position relative to the top left corner of the plate."""
        self.AchkChannel = channel
        """Channel index on the artichoke headstage."""
        self.ID = id
        """The user known ID of the electrode (e.g. 11, 12, ...)"""
        self.Radius = radius
        """The radius of the electrode in µm."""

# geometry data taken from Axion technical documentation available at https://www.axionbiosystems.com/resources
# accessed 20/09/2023
# all plates have the same overall dimensions and all 6, 24, 48, and 96 well plates share the same well geometries over the product palette
# e.g. a 96 well CytoView plate has the same geometry as a 96 well Lumos MEA plate
# As far as I am aware, ClearView plates do not have any electrodes so they are not relevant for this work


class ArrayShape(Enum):
    Grid = 0
    Hourglass = 1


class ElectrodeGeometry:
    """Class to create electrode geometry data for an Axion plate that 
    was used to record the given file.
    See https://www.axionbiosystems.com/resources for the technical documentation used to obtain the values used.

    Classmethods:
        - `CreateNWellPlate`: Wrapper for the other class methods.
        - `Create6WellPlate`: Creates an `ElectrodeGeometry` instance with the appropriate values for a 6 well plate.
        - `Create24WellPlate`: Creates an `ElectrodeGeometry` instance with the appropriate values for a 24 well plate.
        - `Create48WellPlate`: Creates an `ElectrodeGeometry` instance with the appropriate values for a 48 well plate.
        - `Create96WellPlate`: Creates an `ElectrodeGeometry` instance with the appropriate values for a 96 well plate."""

    def __init__(self, pitch: float, diameter: float, areaLength: float, areaWidth: float, shape: ArrayShape, n: int) -> None:
        self.Pitch = pitch
        """The distance between the electrode centers in µm (equal in horizontal and vertical direction)."""
        self.Diameter = diameter
        """The diameter of the electrode in µm."""
        self.Length = areaLength
        """The length of the measuring area in µm."""
        self.Width = areaWidth
        """The width of the measuring area in µm."""
        self.Shape = shape
        """The shape of the measuring area.
            - Grid: square grid of electrodes.
            - Hourglass: top row of 3 electrodes, followed by a row of 2 electrodes, and another row of 3 electrodes."""
        self.Area = areaLength*areaWidth
        """Surface area of the measuring area in µm²"""
        self.N_Electrodes = n
        """The number of electrodes."""
        self.Positions: dict[int, Point] = {}
        """The positions of the electrodes relative to the well center. Indexing starts at the bottom left corner of the area with 11."""
        if shape == ArrayShape.Grid:
            i = int(sqrt(n))
            for l in range(i):
                # defines (x,y) coordinates
                p0 = Point((-i/2+0.5)*pitch, (-i/2+0.5+l)*pitch)
                for m in range(i):
                    self.Positions[10*(l+1)+(m+1)] = p0+Point(m*pitch, 0)
        if shape == ArrayShape.Hourglass:
            # only for 8 electrode, 96 well plates
            i = 3
            for l, (p, i) in enumerate([(Point(-1*pitch, -1*pitch), 3), (Point(-0.5*pitch, 0), 2), (Point(-1*pitch, 1*pitch), 3)]):
                for m in range(i):
                    self.Positions[10+(l+1)+(m+1)] = p + Point(m*pitch, 0)

    @classmethod
    def CreateNWellPlate(cls, n: int) -> Self:
        """Convenience wrapper for the other classmethods. Allows creation of 6, 24, 48, and 96 well plates.

        Args:
            n (`int`): The number of wells.

        Raises:
            `ValueError`: If the number of wells is not supported.

        Returns:
            `ElectrodeGeometry`: An appropriate `ElectrodeGeometry` instance.
        """
        if n not in [6, 24, 48, 96]:
            raise ValueError(f"Number of wells ({n}) cannot be resolved.")
        return getattr(cls, f"Create{n}WellPlate")()

    @classmethod
    def Create6WellPlate(cls):
        """Creates a  `ElectrodeGeometry` instance with the appropriate values for a 6 well plate

        Returns:
            `ElectrodeGeometry`: The instance with appropriate dimensions
        """
        return cls(300, 50, 2100, 2100, ArrayShape.Grid, 64)

    @classmethod
    def Create24WellPlate(cls):
        """Creates a  `ElectrodeGeometry` instance with the appropriate values for a 24 well plate

        Returns:
            `ElectrodeGeometry`: The instance with appropriate dimensions
        """
        return cls(350, 50, 1100, 1100, ArrayShape.Grid, 16)

    @classmethod
    def Create48WellPlate(cls):
        """Creates a  `ElectrodeGeometry` instance with the appropriate values for a 48 well plate

        Returns:
            `ElectrodeGeometry`: The instance with appropriate dimensions
        """
        return cls(350, 50, 1100, 1100, ArrayShape.Grid, 16)

    @classmethod
    def Create96WellPlate(cls):
        """Creates a  `ElectrodeGeometry` instance with the appropriate values for a 96 well plate

        Returns:
            `ElectrodeGeometry`: The instance with appropriate dimensions
        """
        return cls(350, 50, 800, 800, ArrayShape.Hourglass, 8)


class PlateGeometry:
    """Class to create geometry data for an Axion plate that 
    was used to record the given file. Internally creates an appropriate ElectrodeGeometry instance. 
    See https://www.axionbiosystems.com/resources for the technical documentation used to obtain the values used.

    Methods:
        - `GetAbsoluteElectrodePositions`: Returns a dictionary of dictionaries which, for each well, 
        contain the absolute position of each electrode on the plate as an 
        instance of the point class, indexed by the electrode name (as an int).
        - `BakeElectrodes`: Returns a dictionary of lists which, for each well, contain instances
        of the `Electrode` class that holds information about positions, the id, and the channel index.

    Classmethods:
        - `CreateNWellPlate`: Wrapper for the other class methods.
        - `Create6WellPlate`: Creates a `PlateGeometry` instance with the appropriate values for a 6 well plate.
        - `Create24WellPlate`: Creates a `PlateGeometry` instance with the appropriate values for a 24 well plate.
        - `Create48WellPlate`: Creates a `PlateGeometry` instance with the appropriate values for a 48 well plate.
        - `Create96WellPlate`: Creates a `PlateGeometry` instance with the appropriate values for a 96 well plate.
    """

    def __init__(self, sourceSet: BlockVectorSet, roff: float, coff: float, pitch: float, diameter: float, n_wells: int, n_rows: int) -> None:
        """Class to create geometry data for an Axion plate that 
            was used to record the given `BlockVectorSet`. Internally creates an appropriate `ElectrodeGeometry` instance.

        Args:
            sourceSet (`BlockVectorSet`): The `BlockVectorSet` instance that contains the data. The plate geometry will most likely be the same for all BlockVectorSets.
            roff (`float`): Row offset of the top left well
            coff (`float`): Collumn offset of the top left well.
            pitch (`float`): Distance between the centers of two wells (should be identical horizontally and vertically).
            diameter (`float`): Diameter of the well at the top.
            n_wells (`int`): Number of wells on the plate.
            n_rows (`int`): Number of rows of wells.
        """
        self.Length = 127.76
        """The physical length (long side) of the plate in mm."""
        self.Width = 85.48
        """The physical width (short side) of the plate in mm."""
        self.RowOffset = roff
        """The vertical distance to well A1's center from the top left of the plate in mm."""
        self.ColumnOffset = coff
        """The horizontal distance to well A1's center from the top left of the plate in mm."""
        self.Pitch = pitch
        """The distance between two wells (equal in both directions) in mm."""
        self.Diameter = diameter
        """The diameter of a well in mm."""
        self.N_Wells = n_wells
        """The number of wells on the plate."""
        self.ElectrodeGeometry = ElectrodeGeometry.CreateNWellPlate(
            self.N_Wells)
        """An `ElectrodeGeometry` instance appropriate for the current plate type."""
        self.N_Rows = n_rows
        """The number of rows on the plate."""
        self.N_Cols = n_wells//n_rows
        """The number of columns on the plate."""
        self.SourceSet = sourceSet
        """The `BlockVectorSet` instance in which the data is stored that was recorded with the current plate."""
        self.Positions: dict[str, Point] = {}
        """A dictionary of well keys (A1, ...) and `Point` instances that represent the centers of the wells."""
        p0 = Point(self.ColumnOffset, self.RowOffset)
        for l in range(self.N_Rows):
            for m in range(self.N_Cols):
                # check the +1
                self.Positions[f"{chr(l+1+64)}{m+1}"] = p0 + \
                    Point(m*pitch, l*pitch)

    def GetAbsoluteElectrodePositions(self):
        """Generates the absolute positions of each electrode based on the plate and electrode geometries.

        Returns:
            `dict[str, dict[int, Point]]`: A dictionary of well indexes and dictionary values that 
            contain the electrode center indexed by the electrodes id (11, 12, ...).
        """
        ret: dict[str, dict[int, Point]] = {}
        for well, loc in self.Positions.items():
            ret[well] = {elid: loc+elloc.YInv for elid,
                         elloc in self.ElectrodeGeometry.Positions.items()}
        return ret

    def BakeElectrodes(self):
        """Transfers the informations contained in the current instance into a dictionary of `Electrode` instance containing lists.

        Returns:
            `dict[str, list[Electrode]]`: The dictionary containing the lists of `Electrode` instances.
        """
        channelMappings = GetElectrodeMappings(
            self.SourceSet, filterAvailable=False)
        channelMappings = {well: {elid: channel for elid, channel in ids}
                           for well, ids in channelMappings.items()}
        absolutes = self.GetAbsoluteElectrodePositions()
        ret: dict[str, list[Electrode]] = {}
        for well in self.Positions.keys():
            ret[well] = [Electrode(elid, self.ElectrodeGeometry.Positions[elid], absolutes[well][elid],
                                   channelMappings[well][elid], self.ElectrodeGeometry.Diameter/2) for elid in absolutes[well].keys()]
        return ret

    @classmethod
    def CreateNWellPlate(cls, sourceSet: BlockVectorSet, n: int) -> Self:
        """Convenience wrapper for the other classmethods. Allows creation of 6, 24, 48, and 96 well plates.

        Args:
            sourceSet (`BlockVectorSet`): The `BlockVectorSet` instance that contains the data.
            n (`int`): The number of wells.

        Raises:
            `ValueError`: If the number of wells is not supported.

        Returns:
            `PlateGeometry`: An appropriate `PlateGeometry` instance.
        """
        if n not in [6, 24, 48, 96]:
            raise ValueError(f"Number of wells ({n}) cannot be resolved.")
        return getattr(cls, f"Create{n}WellPlate")(sourceSet)

    @classmethod
    def Create6WellPlate(cls, sourceSet: BlockVectorSet) -> Self:
        """Creates a `PlateGeometry` instance with the appropriate values for a 6 well plate

        Args:
            sourceSet (`BlockVectorSet`): The `BlockVectorSet` instance that contains the data.

        Returns:
            `PlateGeometry`: The instance with appropriate dimensions
        """
        return cls(sourceSet, 24.74, 27.88, 36.00, 22.00, 6, 2)

    @classmethod
    def Create24WellPlate(cls, sourceSet: BlockVectorSet) -> Self:
        """Creates a `PlateGeometry` instance with the appropriate values for a 24 well plate

        Args:
            sourceSet (`BlockVectorSet`): The `BlockVectorSet` instance that contains the data.

        Returns:
            `PlateGeometry`: The instance with appropriate dimensions.
        """
        return cls(sourceSet, 15.69, 18.83, 18.00, 15.00, 24, 4)

    @classmethod
    def Create48WellPlate(cls, sourceSet: BlockVectorSet) -> Self:
        """Creates a `PlateGeometry` instance with the appropriate values for a 48 well plate

        Args:
            sourceSet (`BlockVectorSet`): The BlockVectorSet instance that contains the data.

        Returns:
            `PlateGeometry`: The instance with appropriate dimensions
        """
        return cls(sourceSet, 10.04, 18.10, 13.08, 10.35, 48, 6)

    @classmethod
    def Create96WellPlate(cls, sourceSet: BlockVectorSet) -> Self:
        """Creates a `PlateGeometry` instance with the appropriate values for a 96 well plate

        Args:
            sourceSet (`BlockVectorSet`): The `BlockVectorSet` instance that contains the data.

        Returns:
            `PlateGeometry`: The instance with appropriate dimensions
        """
        return cls(sourceSet, 11.24, 14.38, 9.00, 8.07, 96, 8)


def GetElectrodePositions(sourceSet: BlockVectorSet) -> dict[str, list[Electrode]]:
    """Creates a `PlateGeometry` instance and returns the baked electrodes. May contain electrodes that were not recorded.

    Args:
        sourceSet (`BlockVectorSet`): The `BlockVectorSet` instance that contains the data.

    Returns:
        dict[str, list[Electrode]]: A dictionary with well ids as keys and lists of `Electrode` instances contained in these wells.
    """
    geometry = PlateTypes.get_electrode_dimensions(
        sourceSet.channel_array.plate_type)
    plate = PlateGeometry.CreateNWellPlate(
        sourceSet, n=geometry[0]*geometry[1])
    return plate.BakeElectrodes()

def GetRelativeArrayContours(sourceSet: BlockVectorSet) -> list[Point]:
    geometry = PlateTypes.get_electrode_dimensions(
        sourceSet.channel_array.plate_type)
    plate = PlateGeometry.CreateNWellPlate(
        sourceSet, n=geometry[0]*geometry[1])
    arrlen = plate.ElectrodeGeometry.Length
    arrwidth = plate.ElectrodeGeometry.Width
    bottomleft = Point(-arrwidth/2, -arrlen/2)
    return [bottomleft, bottomleft.XInv, -bottomleft, bottomleft.YInv]
