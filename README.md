# PyAxion

## Introduction

This project serves as a mostly faithful reimplementation of the official matlab loader
for data produced by Axion Biosystem's AxIS software in the form of .raw and .spk files.

This project is neither funded nor endorsed by Axion Biosystem and thus does not guarantee
functionality and timely updates.

## Features

The current version supports .raw and .spk files of version 1.x <= 1.3. Unlike the original
matlab implementation, this project does not support legacy files of version 0.x but I
would be happy to collaborate on a future inclusion.

This project also contains code to write an older version of .spk files. However, it is currently
not up to date with the new structure of the matlab/python code so it will likely not work.
I might update it in the future but I cannot guarantee it, since I am not sure if the use case
will come up for me. Feel free to open an issue or pull request for any updates an we will see
what we can do.

On a similar veine there is also a rudimentary binding for python-neo and probeinterface that
is unfortunately now outdated. If the interest comes up we can also discuss updating this binding.

## Examples

### Accessing datasets in the file

The `AxisFile` object provides a number of properties that can help you indentify relevant datasets
in the loaded file. Each of the methods returns the appropriate dataset or `None` if it doesn't
exist.

It is unlikely/impossible for multiple dataset types to occur in the same file. A notable
exception would be high and low frequency components of the broad band signal

```python
from pyaxion.axis_reader import AxisFile, ReturnDimension

# use the file as a context manager to properly release the file opened for reading
with AxisFile("example_file.raw") as af:
    # the broad band signal
    dataset = af.raw_voltage
    # check the output for validity
    if dataset is not None:
        ...
    # the high-pass filtered portion of the broad band signal
    dataset = af.broad_band_high
    # contractility data as a continuous waveform
    dataset = af.raw_contractility
    # discontinous spike events
    dataset = af.spikes
    # discontinuous local field potential events
    dataset = af.lfp_events
```

The returned objects are datasets that define further methods to load the data. They do not
directly represent the raw data array and as such do not create a large loading overhead.

### Reading raw voltage data from a file

Once you have obtained your dataset you will want to load the raw data from it. This can
be either spikes or continuous waveforms. Loading data creates numpy object arrays that
hold further containers that combine metadata about the raw data like electrode positions
with the actual data array. This section explains how to create and work with these object
arrays to obtain the actual numpy arrays containing the data. This example considers
continuous waveform data, but it works equivalently with spike data and other types of continuous
data.

Data can be loaded in as a 4-D channel array structure. Data is indexed as well
row, well column, electrode column, electrode row.

```python
from pyaxion.axis_reader import AxisFile, ReturnDimension

# use the file as a context manager to properly release the file opened for reading
with AxisFile("example_file.raw") as af:
    # numpy array of shape n_well_rows, n_well_cols, n_el_cols, n_el_rows
    data = af.raw_voltage.load_raw_data(dimension = ReturnDimension.BYELECTRODE)
```

The returned array is an `object` numpy array where the objects represent datacontainers that can
be of several types:
For continuous waveform data (e.g. regular traces):
- `VoltageWaveform` object defining the `.get_voltage_vector()` method
- `ContractilityWaveform` object defining the `.get_contractility_vector()` method

Both classes also define a `get_time_vector()` method and a combined method for their respective
data vector methods that returns a time axis or a tuple of the data and the time axis.

For discontinuous event data (e.g. spikes):
- `Spike_v1` object defining the `.get_voltage_vector()` method that returns the spike waveforms

```python
with AxisFile("example_file.raw") as af:
    # numpy array of shape n_well_rows, n_well_cols, n_el_cols, n_el_rows
    data = af.raw_voltage.load_raw_data(dimension = ReturnDimension.BYELECTRODE)

    # numpy array of shape n_samples x sample_rate (typically 12.5 kHz)
    # the data is returned volts
    voltage_vector = data[0,0,0,0].get_voltage_vector()
```

Raw ADC bits can be accessed by calling the `.data` field of waveforms.

The return dimensions can be manipulated by changing the `dimension` argument.
The default argument is `ReturnDimension.BYPLATE`
```python
with AxisFile("example_file.raw") as af:
    # numpy array of shape n_well_rows, n_well_cols, n_el_cols, n_el_rows
    data = af.raw_voltage.load_raw_data(dimension = ReturnDimension.BYELECTRODE)
    # numpy array of n_well_rows, n_well_cols
    data = af.raw_voltage.load_raw_data(dimension = ReturnDimension.BYWELL)
    # numpy array of n_wells x n_electrodes_per_well
    data = af.raw_voltage.load_raw_data(dimension = ReturnDimension.BYPLATE)
```

Electrodes are named by their column and row, such that electrode 23 refers to the electrode in
the second column and third row

Wells and electrodes can be specified during loading to reduce the data size.

```python
with AxisFile("example_file.raw") as af:
    # numpy array of shape n_well_rows, n_well_cols, n_el_cols, n_el_rows
    data = af.raw_voltage.load_raw_data(
        wells = "A1,A2,B4,",
        electrodes = "11,12,23,44", # for a plate with 16 electrodes per well
        # alternatively this package also allows lists of integers
        # electrodes = [11,12,23,44] # equivalent to the argument above
        dimension = ReturnDimension.BYELECTRODE)
```

Data can be subsampled during loading. Subsampling is done by simply skipping the appropriate
number of samples, the data is not interpolated. A subsampling factor of 1 results in no
subsampling.

```python
with AxisFile("example_file.raw") as af:
    # numpy array of shape n_well_rows, n_well_cols, n_el_cols, n_el_rows
    data = af.raw_voltage.load_raw_data(
        wells = "A1,A2,B4,",
        electrodes = [11,12,23,44], # for a plate with 16 electrodes per well
        dimension = ReturnDimension.BYELECTRODE),
        subsampling_factor = 2 # only every second sample is loaded
```

The time range of the loaded data can be adjusted during loading as well.

```python
with AxisFile("example_file.raw") as af:
    # numpy array of shape n_well_rows, n_well_cols, n_el_cols, n_el_rows
    data = af.raw_voltage.load_raw_data(
        wells = "A1,A2,B4,",
        electrodes = [11,12,23,44], # for a plate with 16 electrodes per well
        dimension = ReturnDimension.BYELECTRODE),
        time_range = [0, 10], # data from the first 10 seconds
        subsampling_factor = 2 # only every second sample is loaded
```

### Accessing stimulation events

If the recording contains stimulation that was properly flagged using the inverted triangle
marker during recording setup (you cannot change this after the recording is done), the file
will contain stimulation events that mark the beginning of the stimulation. It can be accessed
using

```python
with AxisFile("example_file.raw") as af:
    # list of StimulationEvent instances
    af.stimulation_events
    # timing of the events in seconds
    times = sorted([event.event_time for event in af.stimulation_events])
```

## On the 'pythonicity' of this package

This package was created to make accessing AxIS files easier in python. It was not created
to be the most efficient interface for the data that can be updated relatively easy along with
the original matlab implementation. Hence, it sometimes favors closeness to the matlab source
over traditional pythonic practices. However, it does make some significant deviations in some
places either due to limitations of either of the languages or because of code that would run
extremely poorly in python.

Nevertheless, it isn't out of the question to transform this into a more self contained project
since I am sure there are a number of ways in which the loading of the data can be made quicker
and more pythonic. Feel free to use this project as a stepping stone or to create pull requests.
