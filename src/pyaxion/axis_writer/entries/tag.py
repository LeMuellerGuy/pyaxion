"""Module containing function to write various types of tags to an Axis file.

The general byte structure of a tag is as follows:
36 bytes for the tag entry,
optionally 24 bytes for an EventTag,
followed by the specific tag data
plus some padding to align the next tag to (what I assume is) a 4-byte boundary.

When the tags are read from the file, by default only the tag with the highest revision number
is read. Thus, if we want to save the previous revisions, we have to supply the axis file to
read them from the raw file. The revisions are grouped by their GUID and tag type.
Thus the last entry in the _entryNodes list is the tag read by default.

As far as I know, tags do not have to be in any specific order in the file."""

from typing import TYPE_CHECKING

import numpy as np

from ...axis_reader.axis_file import AxisFile
from ...axis_reader.helper_functions.group_structs import LedGroup
from ...axis_reader.helper_functions.parse_guid import encode_guid
from ...axis_reader.plate_management.led_position import LedPosition
from ...axis_reader.tags.stimulation.stimulation_event import StimulationEvent
from ...axis_reader.tags.tag import (Annotation, EventTag, LeapInductionEvent,
                                 StimulationChannels, StimulationEvent,
                                 StimulationLeds, StimulationWaveform, Tag,
                                 WellInformation)
from ...axis_writer.entries.block_vector import WriteChannelMapping
from pyaxion.axis_writer.entries.date_time import WriteDateTime

if TYPE_CHECKING:
    from ..axis_file import AxisFileWriter


def WriteString(string:str, file:'AxisFileWriter'):
    """Writes a string to the file, prefixed by its length as a 4-byte integer."""
    encoded_string = string.encode('utf-8')
    file.write(len(encoded_string).to_bytes(4, 'little', signed=True) + encoded_string)

def WriteTagEntry(tag:Tag, file:'AxisFileWriter', node_index:int = 0):
    start = file.tell()
    # write as uint16
    file.write(np.uint16(tag.type.value).tobytes())
    tagEntry = tag.entry_nodes[node_index]
    WriteDateTime(tagEntry.CreationDate, file)
    file.write(encode_guid(tag.tagGuid))
    file.write(tagEntry.RevisionNumber.tobytes())
    return file.tell() - start

def WriteEventTag(tag:EventTag, file:'AxisFileWriter', node_index:int = 0):
    entrySize = WriteTagEntry(tag, file, node_index)
    start = file.tell()
    file.write(tag.sampling_frequency.tobytes())
    file.write(tag.event_time_sample.tobytes())
    file.write(tag.event_duration_sample.tobytes())
    return file.tell() - start + entrySize

def WriteAnnotation(tag:Annotation, writer:'AxisFileWriter', reader:AxisFile = None):
    if reader is not None:
        for node in tag.entry_nodes[:-1]:
            annotation = Annotation(reader.FileID, node)
            annotation.add_node(node)
            WriteAnnotation(annotation, writer)
    node_index = len(tag.entry_nodes) - 1
    start = writer.tell()
    WriteEventTag(tag, writer, node_index)
    writer.write(tag.well_column.to_bytes(1, 'little', signed=False))
    writer.write(tag.well_row.to_bytes(1, 'little', signed=False))
    writer.write(tag.electrode_column.to_bytes(1, 'little', signed=False))
    writer.write(tag.electrode_row.to_bytes(1, 'little', signed=False))
    WriteString(tag.note_text, writer)
    size = writer.tell() - start
    entry_record = tag.entry_nodes[node_index].entry_record
    if size < entry_record.length:
        writer.write(b'\x00' * int((entry_record.length - size)))
    writer.WriteEntry(tag.entry_nodes[node_index].entry_record)

def WriteLeapInductionEvent(tag:LeapInductionEvent, writer:'AxisFileWriter', reader:AxisFile = None):
    if reader is not None:
        for node in tag.entry_nodes[:-1]:
            leapEvent = LeapInductionEvent(reader.FileID, node)
            leapEvent.add_node(node)
            WriteLeapInductionEvent(leapEvent, writer)
    node_index = len(tag.entry_nodes) - 1
    start = writer.tell()
    WriteTagEntry(tag, writer, node_index)
    writer.write(tag.current_version.to_bytes(2, 'little', signed=False))
    # Only the first uint16 is used, so write a second dummy uint16 (as in original code)
    writer.write((0).to_bytes(2, 'little', signed=False))
    WriteDateTime(tag.leap_induction_start_time, writer)
    writer.write(np.uint64(tag.leap_induction_duration/1e7).tobytes())
    writer.write(tag.plate_type.tobytes())
    writer.write(len(tag.leaped_channels).to_bytes(4, 'little', signed=False))
    for channel in tag.leaped_channels:
        WriteChannelMapping(channel, writer)
    size = writer.tell() - start
    entry_record = tag.entry_nodes[node_index].entry_record
    if size < entry_record.length:
        writer.write(b'\x00' * int((entry_record.length - size)))
    writer.WriteEntry(tag.entry_nodes[node_index].entry_record)

def WriteWellInformation(tag:WellInformation, writer:'AxisFileWriter', reader:AxisFile = None):
    if reader is not None:
        for node in tag.entry_nodes[:-1]:
            reader.seek_entry_record(node.entry_record)
            wellInfo = WellInformation(reader.FileID, node)
            wellInfo.add_node(node)
            WriteWellInformation(wellInfo, writer)
    node_index = len(tag.entry_nodes) - 1
    start = writer.tell()
    WriteTagEntry(tag, writer, node_index)
    
    writer.write(tag.well_column.tobytes())
    writer.write(tag.well_row.tobytes())
    writer.write(np.uint8(0).tobytes()) # electrodes
    writer.write(np.uint8(0).tobytes()) # electrodes

    # Write well type as a single uint8 (bit 0: isOn, bit 1: isControl)
    well_type = (int(tag.is_on) & 1) | ((int(tag.is_control) & 1) << 1)
    writer.write(np.uint8(well_type).tobytes())

    writer.write(tag.red.tobytes())
    writer.write(tag.green.tobytes())
    writer.write(tag.blue.tobytes())

    WriteString(tag.treatment_what, writer)
    WriteString(tag.additional_information, writer)

    writer.write(tag.treatment_how_much_base_value.tobytes())
    writer.write(tag.treatment_how_much_unit_exponent.tobytes())
    WriteString(tag.treatment_how_much_base_unit, writer)
    size = writer.tell() - start
    entry_record = tag.entry_nodes[node_index].entry_record
    # The files written by the Axis software seem to sometimes have zero padding
    # we just keep the padding to be compatible with the original files
    if size < entry_record.length:
        writer.write(b'\x00' * int((entry_record.length - size)))  # Pad with zeros if necessary
    writer.WriteEntry(entry_record)

def WriteStimulationChannels(tag:StimulationChannels, writer:'AxisFileWriter', reader:AxisFile = None):
    if reader is not None:
        for node in tag.entry_nodes[:-1]:
            stimChannels = StimulationChannels(reader.FileID, node)
            stimChannels.add_node(node)
            WriteStimulationChannels(stimChannels, writer)
    node_index = len(tag.entry_nodes) - 1
    start = writer.tell()
    WriteTagEntry(tag, writer, node_index)
    writer.write(np.uint16(StimulationChannels.current_version).tobytes())
    writer.write(np.uint16(0).tobytes())
    writer.write(np.uint32(len(tag.channel_groups)).tobytes())
    for group in tag.channel_groups:
        # Write group ID and plate type as uint32
        writer.write(group.id.tobytes())
        writer.write(group.plate_type.tobytes())
        # Write number of channels as uint32
        writer.write(np.uint32(len(group.mappings)).tobytes())
        # Write each channel mapping
        for channel in group.mappings:
            WriteChannelMapping(channel, writer)
    writer.WriteEntry(tag.entry_nodes[node_index].entry_record)

def WriteStimulation(tag:StimulationEvent, writer:'AxisFileWriter', reader:AxisFile = None):
    if reader is not None:
        for node in tag.entry_nodes[:-1]:
            stimEvent = StimulationEvent(reader.FileID, node)
            stimEvent.add_node(node)
            WriteStimulation(stimEvent, writer)
    node_index = len(tag.entry_nodes) - 1
    start = writer.tell()
    WriteEventTag(tag, writer, node_index)
    if tag.waveform_tag == ''\
        and tag.channels_tag == ''\
        and tag.event_data == np.uint16('FFFF')\
        and tag.sequence_number == np.uint16('FFFF'):
        # Dummy version number
        writer.write(np.uint16('FFFF').tobytes())
        writer.write(np.uint16(0).tobytes())
        writer.WriteEntry(tag.entry_nodes[node_index].entry_record)
        return
    
    writer.write(np.uint16(StimulationEvent.current_version).tobytes())
    writer.write(np.uint16(0).tobytes())  # Reserved short
    
    # Write waveformTag and channelsTag as GUIDs (16 bytes each)
    writer.write(encode_guid(tag.waveform_tag))
    writer.write(encode_guid(tag.channels_tag))

    # Write eventData and sequenceNumber as uint16
    writer.write(tag.event_data.tobytes())
    writer.write(tag.sequence_number.tobytes())
    size = writer.tell() - start
    entry_record = tag.entry_nodes[node_index].entry_record
    if size < entry_record.length:
        writer.write(b'\x00' * int((entry_record.length - size)))
    writer.WriteEntry(tag.entry_nodes[node_index].entry_record)

def WriteStimulationBlock(stim_event_data:StimulationEventData, writer:'AxisFileWriter'):
    # Write fields to disk
    writer.write(stim_event_data.ID.tobytes())
    writer.write(np.uint16(0).tobytes())  # Reserved short
    writer.write(stim_event_data.StimDuration.tobytes())
    writer.write(stim_event_data.ArtifactEliminationDuration.tobytes())
    writer.write(stim_event_data.ChannelArrayIdList.tobytes())
    WriteString(stim_event_data.Description, writer)

def WriteStimulationWaveform(tag:StimulationWaveform, writer:'AxisFileWriter', reader:AxisFile = None):
    if reader is not None:
        for node in tag.entry_nodes[:-1]:
            stimWaveform = StimulationWaveform(reader.FileID, node)
            stimWaveform.add_node(node)
            WriteStimulationWaveform(stimWaveform, writer)
    node_index = len(tag.entry_nodes) - 1
    start = writer.tell()
    WriteTagEntry(tag, writer, node_index)
    if len(tag.tag_blocks) == 0:
        # Dummy version number
        writer.write(np.uint16('FFFF').tobytes())
        writer.write(np.uint16(0).tobytes()) # reserved short
        writer.WriteEntry(tag.entry_nodes[node_index].entry_record)
        return
    writer.write(np.uint16(StimulationWaveform.current_version).tobytes())
    writer.write(np.uint16(len(tag.tag_blocks)).tobytes())  # Reserved short
    for block in tag.tag_blocks:
        WriteStimulationBlock(block, writer)
    size = writer.tell() - start
    entry_record = tag.entry_nodes[node_index].entry_record
    if size < entry_record.length:
        writer.write(b'\x00' * int((entry_record.length - size)))
    writer.WriteEntry(tag.entry_nodes[node_index].entry_record)

def WriteLedPosition(pos:LedPosition, writer:'AxisFileWriter'):
    writer.write(pos.well_row.tobytes())
    writer.write(pos.well_column.tobytes())
    writer.write(pos.led_color.value.to_bytes(2, 'little', signed=False))

def WriteLedGroup(group:LedGroup, writer:'AxisFileWriter'):
    """Writes a LedGroup to the Axis file."""
    writer.write(group.id.tobytes())
    writer.write(group.plate_type.tobytes())
    # Write number of mappings as uint32
    writer.write(np.uint32(len(group.mappings)).tobytes())
    for pos in group.mappings:
        WriteLedPosition(pos, writer)

def WriteStimulationLed(tag:StimulationLeds, writer:'AxisFileWriter', reader:AxisFile = None):
    if reader is not None:
        for node in tag.entry_nodes[:-1]:
            stimLed = StimulationLeds(reader.FileID, node)
            stimLed.add_node(node)
            WriteStimulationLed(stimLed, writer)
    node_index = len(tag.entry_nodes) - 1
    start = writer.tell()
    WriteTagEntry(tag, writer, node_index)
    if len(tag.led_groups) == 0:
        # Dummy version number
        writer.write(np.uint16('FFFF').tobytes())
        writer.WriteEntry(tag.entry_nodes[node_index].entry_record)
        return
    writer.write(np.uint16(StimulationLeds.current_version).tobytes())
    writer.write(len(tag.led_groups).to_bytes(2, 'little', signed=False))
    for group in tag.led_groups:
        WriteLedGroup(group, writer)
    size = writer.tell() - start
    entry_record = tag.entry_nodes[node_index].entry_record
    if size < entry_record.length:
        writer.write(b'\x00' * int((entry_record.length - size)))
    writer.WriteEntry(tag.entry_nodes[node_index].entry_record)

def WriteTag(tag:Tag, writer:'AxisFileWriter', reader:AxisFile = None):
    if isinstance(tag, Annotation):
        WriteAnnotation(tag, writer, reader)
    elif isinstance(tag, LeapInductionEvent):
        WriteLeapInductionEvent(tag, writer, reader)
    elif isinstance(tag, WellInformation):
        WriteWellInformation(tag, writer, reader)
    elif isinstance(tag, StimulationChannels):
        WriteStimulationChannels(tag, writer, reader)
    elif isinstance(tag, StimulationEvent):
        WriteStimulation(tag, writer, reader)
    elif isinstance(tag, StimulationWaveform):
        WriteStimulationWaveform(tag, writer, reader)
    elif isinstance(tag, StimulationLeds):
        WriteStimulationLed(tag, writer, reader)
    elif type(tag) is Tag:
        if reader is not None:
            for node in tag.entry_nodes[:-1]:
                stimLed = StimulationLeds(reader.FileID, node)
                stimLed.add_node(node)
                WriteStimulationLed(stimLed, writer)
        node_index = len(tag.entry_nodes) - 1
        WriteTagEntry(tag, writer, node_index)
        writer.WriteEntry(tag.entry_nodes[node_index].entry_record)
    else:
        raise TypeError(f"Unsupported tag type: {type(tag)}")
