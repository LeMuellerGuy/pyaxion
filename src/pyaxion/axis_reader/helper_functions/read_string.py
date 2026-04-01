from io import BufferedReader

import numpy as np


def read_string(fileID:BufferedReader):
    string_length = np.fromfile(fileID, np.int32, 1)[0]
    return fileID.read(string_length).decode('utf-8').rstrip("\x00")
