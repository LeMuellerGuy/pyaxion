from io import BufferedReader

from numpy import fromfile, int64, uint16, uint32

from ..tag import Tag

from ...entries.tag_entry import TagEntry
from ...helper_functions.group_structs import ChannelGroup
from ...plate_management.channel_mapping import ChannelMapping


class StimulationChannels(Tag):
    """
    StimulationChannels: File data that enumerates channels used in a stimulation
    """
    CurrentVersion = 0
    MinArraySize = int64(20)

    def __init__(self, file_id:BufferedReader, raw_tag:TagEntry):
        super().__init__(raw_tag.tag_guid)

        # Move to the correct location in the file
        start = int64(raw_tag.start + TagEntry.BASE_SIZE)
        seek_result = file_id.seek(start,0)

        tag_start = int64(raw_tag.start)
        tag_end = int64(tag_start + raw_tag.entry_record.length)

        if seek_result == 0:
            version = fromfile(file_id, dtype=uint16, count=1)[0]
            if version == StimulationChannels.CurrentVersion:
                fromfile(file_id, dtype=uint16, count=1)  # Reserved short
                self.channel_groups = []

                array = 1
                pos = int64(file_id.tell())

                while (tag_end - pos) >= StimulationChannels.MinArraySize:
                    id_ = fromfile(file_id, dtype=uint32, count=1)[0]
                    plate_type = fromfile(file_id, dtype=uint32, count=1)[0]

                    num_channels = fromfile(file_id, dtype=uint32, count=1)[0]
                    channels = [ChannelMapping.from_file(file_id) for _ in range(num_channels)]

                    self.channel_groups.append(ChannelGroup(id_, plate_type, channels))

                    array += 1
                    pos = int64(file_id.tell())
            else:
                self.channel_groups:list[ChannelGroup] = []
                print('Stimulation channels version not supported')
        else:
            raise ValueError('Encountered an error while loading' \
                             f'StimulationChannels {raw_tag.tag_guid}')

        if file_id.tell() > (tag_start + raw_tag.entry_record.length):
            print('File may be corrupted')
