from typing import TYPE_CHECKING
from copy import copy, deepcopy
from numbers import Number
from typing import Any, Iterable
import numpy as np
from pyaxion.axis_reader.block_vector.header import BlockVectorHeader
from pyaxion.axis_reader.block_vector.header_extension import BlockVectorHeaderExtension
from pyaxion.axis_reader.block_vector.set import BlockVectorSet
from pyaxion.axis_reader.entries.channel_array import ChannelArray
from pyaxion.axis_reader.entries.entry_record import EntryRecord
from pyaxion.axis_reader.entries.entry_record_id import EntryRecordID
from pyaxion.axis_reader.plate_management.channel_mapping import ChannelMapping
from pyaxion.axis_writer.entries.DateTime import WriteDateTime

from pyaxion.axis_reader.Waveforms.Spike_v1 import Spike_v1
from pyaxion.axis_reader.Waveforms.Waveform import Waveform
from tqdm import tqdm

if TYPE_CHECKING:
    from ..axis_file import AxisFileWriter

def WriteChannelMapping(channel_mapping:ChannelMapping, file:'AxisFileWriter'):
    """
    Serializes the attributes of a ChannelMapping object and writes them as bytes to a binary file.
    Args:
        channel_mapping (ChannelMapping): The ChannelMapping instance containing 
            mapping attributes to serialize.
        file (BufferedWriter): The binary file object to which the serialized data will be written.
    Raises:
        AttributeError: If channel_array does not have expected attributes.
        TypeError: If file is not a BufferedWriter.
    """

    # Write each attribute of ChannelMapping as bytes to the file
    file.write(int(channel_mapping.well_column).to_bytes(1, 'little', signed=False))
    file.write(int(channel_mapping.well_row).to_bytes(1, 'little', signed=False))
    file.write(int(channel_mapping.electrode_column).to_bytes(1, 'little', signed=False))
    file.write(int(channel_mapping.electrode_row).to_bytes(1, 'little', signed=False))
    file.write(int(channel_mapping.channel_achk).to_bytes(1, 'little', signed=False))
    file.write(int(channel_mapping.channel_index).to_bytes(1, 'little', signed=False))
    file.write(int(channel_mapping.aux_data).to_bytes(2, 'little', signed=False))

def WriteChannelArray(channel_array:ChannelArray, file:'AxisFileWriter') -> EntryRecord:
    """
    Serializes a ChannelArray object to a binary file.
    Args:
        channel_array (ChannelArray): The ChannelArray instance to serialize.
        file (BufferedWriter): The binary file object to write to.
    Raises:
        AttributeError: If channel_array does not have expected attributes.
        TypeError: If file is not a BufferedWriter.
    """
    start = file.tell()
    # Write plate type as 4 bytes
    file.write(channel_array.plate_type.to_bytes(4, 'little'))
    # Write number of channels as 4 bytes
    file.write(len(channel_array.channels).to_bytes(4, 'little'))

    # Write each ChannelMapping using the provided function
    for channel_mapping in channel_array.channels:
        WriteChannelMapping(channel_mapping, file)
    record = copy(channel_array.entry_record)
    record.length = file.tell() - start
    return record

def WriteBlockVectorHeader(bvh: BlockVectorHeader, file: 'AxisFileWriter'):
    file.write(bvh.sampling_frequency.tobytes())
    file.write(bvh.voltage_scale.tobytes())
    WriteDateTime(bvh.file_start_time, file)
    WriteDateTime(bvh.experiment_start_time, file)
    file.write(bvh.first_block.tobytes())
    file.write(bvh.num_channels_per_block.tobytes())
    file.write(bvh.num_samples_per_block.tobytes())
    file.write(bvh.block_header_size.tobytes())
    # the size of the header is fixed so we don't need to adjust the entry record
    return bvh.entry_record

def WriteBlockHeaderExtension(bvhe: BlockVectorHeaderExtension, file: 'AxisFileWriter'):
    start = file.tell()
    file.write(bvhe.extension_version_major.tobytes())
    file.write(bvhe.extension_version_minor.tobytes())
    file.write(bvhe.data_type.value.to_bytes(2, "little", signed=False))
    WriteDateTime(bvhe.added, file)
    WriteDateTime(bvhe.modified, file)
    name_bytes = bvhe.name.encode('utf-8')
    name_bytes = name_bytes.ljust(BlockVectorHeaderExtension._maxNameChar, b'\x00')
    file.write(name_bytes)
    description_bytes = bvhe.description.encode('utf-8')
    # Calculate remaining length for description
    desc_len = start + int(bvhe.entry_record.length) - file.tell()
    description_bytes = description_bytes.ljust(desc_len, b'\x00')
    file.write(description_bytes)
    # the size of the header extension is fixed so we don't need to adjust the entry record
    return bvhe.entry_record

def WriteData(waveform_data:np.ndarray[Any|np.int16]|Iterable[Waveform]|Iterable[Spike_v1],
              file:'AxisFileWriter', bvs:BlockVectorSet, channels:np.ndarray = None):
    bvs = deepcopy(bvs)
    el = next(iter(waveform_data))
    while isinstance(el, (Iterable, np.ndarray)):
        el = next(iter(el))
    if type(el) is Waveform: # Spike_v1 is a subclass of Waveform so we need to check specifically for Waveform
        channels = np.array([bvs.channel_array.LookupChannel(el.Channel.ChannelAchk,
                                                            el.Channel.ChannelIndex)
                                                            for el in waveform_data.flat], dtype = int)
        waveform_data = np.array([el.data for el in waveform_data])
        el = waveform_data[0]
    if isinstance(el, Number):
        assert channels is not None
        mask = np.argsort(channels)
        if waveform_data.dtype != np.int16:
            waveform_data /= bvs.header.voltage_scale
            waveform_data.astype(np.int16)  # convert to ADC bits
        # reorder such that channels are sorted and then reshape such that each channel is after the other
        waveform_data = waveform_data[mask, :].ravel().tobytes()
    elif isinstance(el, Spike_v1):
        waveform_data:np.ndarray[Spike_v1]
        byte_squence = None
        # the order of the spikes is not important since they are reordered on read
        # using the first couple bytes that represent the channel index and channel achk
        def flatten_spikes(wf_data:np.ndarray[Spike_v1]|np.ndarray[list[Spike_v1]]):
            """Flattens the spikes in the waveform data."""
            flattened = [[spike] if isinstance(spike, Spike_v1) else spike
                         for spike in wf_data.flat]
            unpacked = [spike for spike_list in filter(lambda s: s is not None, flattened)
                          for spike in spike_list]
            return np.array(sorted(unpacked, key=lambda s: s.start), dtype=object)
        flat_spikes = flatten_spikes(waveform_data)
        with tqdm(total=len(flat_spikes), desc="Writing spikes") as pbar:
            for spike_list in waveform_data.flat:
                if spike_list is None:
                    continue
                if not isinstance(spike_list, list):
                    spike_list = [spike_list]
                for spike in spike_list:
                    bytes_ = np.int64(spike.Start*bvs.header.sampling_frequency).tobytes()\
                        + np.uint8(spike.Channel.ChannelIndex).tobytes()\
                        + np.uint8(spike.Channel.ChannelAchk).tobytes()\
                        + np.uint32(spike.TriggerSampleOffset).tobytes()\
                        + np.float64(spike.StandardDeviation).tobytes()\
                        + np.float64(spike.ThresholdMultiplier).tobytes()\
                        + spike.Data.tobytes()
                    if not byte_squence:
                        byte_squence = bytes_
                    else:
                        byte_squence += bytes_
                    pbar.update(1)
        waveform_data = byte_squence
    # bvs.ChannelArray._channels = [bvs.ChannelArray.Channels[channel] for channel in channels]
    if isinstance(el, Spike_v1):
        bvs.header.num_channels_per_block = np.uint32(1)
    else:
        bvs.header.num_channels_per_block = np.uint32(channels.size)
    header_start = file.tell()
    bvdata_entry = EntryRecord(EntryRecordID.BlockVectorData, np.uint64(len(waveform_data)))
    # placeholder value
    bvs.header.first_block = np.uint64(0)
    bvh_entry = WriteBlockVectorHeader(bvs.header, file)
    file.WriteEntry(bvh_entry)
    charr_entry = WriteChannelArray(bvs.channel_array, file)
    file.WriteEntry(charr_entry)
    file.CopyNotes(bvs.source_file)
    bvh_ext_entry = WriteBlockHeaderExtension(bvs.header_extension, file)
    file.WriteEntry(bvh_ext_entry)
    first_block = np.uint64(file.tell())
    # we adjust the starting position of the first block in the header after writing
    # additional entries
    file.seek(header_start + 44)
    file.write(first_block.tobytes(), strict = False)
    file.seek(first_block)
    # write the waveform data
    file.write(waveform_data)
    file.WriteEntry(bvdata_entry)
