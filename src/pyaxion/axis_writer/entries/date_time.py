from typing import TYPE_CHECKING
from pyaxion.axis_reader.helper_functions.date_time import DateTime
if TYPE_CHECKING:
    from pyaxion.axis_writer.axis_file import AxisFileWriter

def WriteDateTime(datetime:DateTime, file:'AxisFileWriter'):
    file.write(datetime.year.tobytes())
    file.write(datetime.month.tobytes())
    file.write(datetime.day.tobytes())
    file.write(datetime.hour.tobytes())
    file.write(datetime.minute.tobytes())
    file.write(datetime.second.tobytes())
    file.write(datetime.millisecond.tobytes())