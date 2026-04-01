from typing import Iterable, Union

import numpy as np

from ..block_vector.set import ReturnDimension


def _isscalar(__num):
    return isinstance(__num, (float, int))

class LoadArgs:
    """Helper class for parsing and creating default arguments for loading functions."""
    delimiter = ','

    by_plate_dimensions = 1
    by_well_dimensions = 3
    by_electrode_dimensions = 5

    default_kwargs = {
        "subsampling_factor": 1,
    }

    def __init__(self, wells:str=None, electrodes:str=None,
                 timespan:Iterable[int]=None, dimensions:int=None,
                 **kwargs):
        # initialize default kwarg fields so type hints can work properly
        self.subsampling_factor = self.default_kwargs["subsampling_factor"]
        # replaced the original varargin iteration because python is not a stupid language
        self.wells = self.parse_well(wells, default="all")
        self.electrodes = self.parse_electrode(electrodes, default="all")
        self.timespan = self.parse_timespan(timespan, default="all")
        self.dimensions = self.parse_dimensions(dimensions, default=0)
        # this is originally implemented through the "expansion" argument
        # but matlab is unable to handle keyword arguments
        self.__dict__.update({k:v for k,v in kwargs.items() if k in self.default_kwargs})

    @staticmethod
    def parse_well(argument:str|None, default="all"):
        if not argument:
            argument = default
        out:list[list[int]] = []
        if str(argument).lower() == 'all':
            out = 'all'
        elif isinstance(argument, str):
            canonical_arg = argument.upper().replace(' ', '')
            while canonical_arg is not None:
                if  len(canonical_arg) >= 2 \
                    and \
                    (
                        canonical_arg[0].isalpha() and
                        canonical_arg[1].isdigit()
                    ):
                    split = canonical_arg.split(LoadArgs.delimiter, 1)
                    if len(split) > 1:
                        next_well = split[0]
                        canonical_arg = split[1]
                    else:
                        next_well = split[0]
                        canonical_arg = None
                    next_well = next_well.strip()
                    # while matlab's char() converts to a char type, performing
                    # arithmetic on chars, converts them to utf-8 codes
                    # which is also what python's ord() does
                    out.append([int(next_well[1:]), ord(next_well[0]) - ord('A') + 1])
                else:
                    raise ValueError(f"Invalid well argument: {argument}. "
                                     f"Expected a string of the format 'A1,B2,...' or 'all'.")
        else:
            raise ValueError(f"Invalid well argument: {argument}. "
                             f"Expected a string of the format 'A1,B2,...' or 'all'.")
        return out

    @staticmethod
    def parse_electrode(argument:Iterable[int]|None, default="all"):
        if not argument:
            return default
        out = []
        if str(argument).lower() == 'all':
            out = 'all'
        elif _isscalar(argument) and argument == -1:
            out = 'none'
        elif _isscalar(argument) and argument > 10:
            out = [int(argument // 10), int(argument % 10)]
        elif issubclass(type(argument), Iterable):
            for electrode in argument:
                out.append([int(electrode // 10), int(electrode % 10)])
            out:list[list[int]] = np.array(out).squeeze().tolist()
        elif isinstance(argument, str):
            if argument.strip() == '-1' or argument.lower() == 'none':
                out = 'none'
                return out

            canonical_arg = argument.upper().replace(' ', '')

            while canonical_arg:
                if  len(canonical_arg) >= 2 \
                    and \
                    (
                        canonical_arg[0].isdigit() and
                        canonical_arg[1].isdigit()
                    ):
                    t = canonical_arg.split(',', 1)
                    if len(t) > 1:
                        next_well = t[0]
                        canonical_arg = t[1]
                    else:
                        next_well = t[0]
                        canonical_arg = None
                    next_well = next_well.strip()
                    out.append([int(next_well[0]), int(next_well[1])])
                else:
                    raise ValueError(f"Invalid electrode argument: {argument}. "
                                     "Expected a string of the format '11,12,...' or"
                                     "'all' or 'none'.")
        return out

    @staticmethod
    def parse_timespan(argument:Union[Iterable[Union[int, float]], int, float, None],
                       default="all"):
        if argument is None:
            return default
        if _isscalar(argument):
            return []
        if issubclass(type(argument), Iterable):
            try:
                ret = tuple(argument)
            except TypeError as e:
                raise ValueError("Invalid timespan argument. Expected a scalar or an" \
                                "iterable of scalars.") from e
            assert len(ret) == 2,\
                ValueError("Timespan argument must be a scalar or an iterable of two scalars.")
            assert ret[1] > ret[0],\
                ValueError("Timespan must be an increasing range.")
            return ret
        raise ValueError("Invalid timespan argument. Expected a scalar or an" \
        "iterable of scalars.")

    @staticmethod
    def parse_dimensions(argument:int|ReturnDimension|None, default=0):
        if argument is None:
            return default
        if _isscalar(argument) and argument in [LoadArgs.by_plate_dimensions,
                                                 LoadArgs.by_well_dimensions,
                                                 LoadArgs.by_electrode_dimensions,
                                                 ReturnDimension.DEFAULT]:
            return argument
        else:
            raise ValueError("Invalid dimensions argument. Expected one of the following values: "\
            f"{LoadArgs.by_plate_dimensions}, {LoadArgs.by_well_dimensions}, "\
                f"{LoadArgs.by_electrode_dimensions}.")
