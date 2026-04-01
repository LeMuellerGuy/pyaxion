import numpy as np

class DateTime:
    Size = 14
    def __init__(self, aFileID):
        self.year = np.fromfile(aFileID, dtype=np.uint16, count=1)[0]
        self.month = np.fromfile(aFileID, dtype=np.uint16, count=1)[0]
        self.day = np.fromfile(aFileID, dtype=np.uint16, count=1)[0]
        self.hour = np.fromfile(aFileID, dtype=np.uint16, count=1)[0]
        self.minute = np.fromfile(aFileID, dtype=np.uint16, count=1)[0]
        self.second = np.fromfile(aFileID, dtype=np.uint16, count=1)[0]
        self.millisecond = np.fromfile(aFileID, dtype=np.uint16, count=1)[0]

    def to_date_time_vect(self):
        f_seconds = self.second + (self.millisecond * 1e-3)
        date_vector = np.array([self.year, self.month, self.day,
                                self.hour, self.minute, f_seconds],
                                dtype=np.double)
        return date_vector

    def to_date_time_number(self):
        date_vector = self.to_date_time_vect()
        datenumber = np.datetime64('-'.join(map(str, date_vector[:3]))) \
            + np.timedelta64(int(date_vector[3]), 'h') \
                + np.timedelta64(int(date_vector[4]), 'm') \
                    + np.timedelta64(date_vector[5], 's')
        return datenumber

    def __repr__(self):
        return f"DateTime {self.year}-{self.month:02d}-{self.day:02d} {self.hour:02d}"\
            f":{self.minute:02d}:{self.second:02d}.{self.millisecond:03d}"
