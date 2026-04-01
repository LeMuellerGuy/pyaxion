from io import BufferedReader
from os.path import getsize

import numpy as np

from ..entries.tag_entry import TagEntry
from ..helper_functions.read_string import read_string
from .tag import Tag


class WellInformation(Tag):
    """WellInformation: Class that describes the platemap data for a single well"""
    def __init__(self, file_id:BufferedReader, raw_tag:TagEntry):
        super().__init__(raw_tag.tag_guid)

        start = raw_tag.start + TagEntry.BASE_SIZE
        end = raw_tag.start + raw_tag.entry_record.length
        file_id.seek(start)

        if start < getsize(file_id.name):
            self.well_column:np.uint8 = np.fromfile(file_id, np.uint8, 1)[0]
            self.well_row:np.uint8 = np.fromfile(file_id, np.uint8, 1)[0]
            electrode_column:np.uint8 = np.fromfile(file_id, np.uint8, 1)[0]
            electrode_row:np.uint8 = np.fromfile(file_id, np.uint8, 1)[0]

            # Verify well coordinates
            if self.well_column == 0 or self.well_row == 0:
                raise ValueError(f'WellInformationTag {raw_tag.tag_guid} contains invalid data')

            # Electrode position should always be broadcast to well here
            if electrode_column != 0 or electrode_row != 0:
                print('File may be corrupted')

            well_type:np.uint8 = np.fromfile(file_id, np.uint8, 1)[0]
            self.is_on = bool(well_type & 1)
            self.is_control = bool(well_type & 2)

            bytes_remaining = end - file_id.tell()

            # We should have at least 12 bytes remaining: 3 for RGB, at least 8 for empty strings,
            # and 1 for TreatmentHowMuchUnitExponent
            if bytes_remaining >= 12:
                self.red:np.uint8 = np.fromfile(file_id, np.uint8, 1)[0]
                self.green:np.uint8 = np.fromfile(file_id, np.uint8, 1)[0]
                self.blue:np.uint8 = np.fromfile(file_id, np.uint8, 1)[0]

                # User Treatment Data
                self.treatment_what = read_string(file_id)
                self.additional_information = read_string(file_id)

                bytes_remaining = end - file_id.tell()

                # Make sure we have at least 13 bytes remaining - 8 for TreatmentHowMuchBaseValue,
                # 1 for exponent, 4 for empty string
                if bytes_remaining > 9:
                    self.treatment_how_much_base_value:np.double =\
                        np.fromfile(file_id, np.double, 1)[0]
                    self.treatment_how_much_unit_exponent:np.int8 =\
                        np.fromfile(file_id, np.int8, 1)[0]
                    self.treatment_how_much_base_unit = read_string(file_id)
                else:
                    self.treatment_how_much_base_value = np.double(0.0)
                    self.treatment_how_much_unit_exponent = np.int8(0)
                    self.treatment_how_much_base_unit = ''
                    print(f'Tag {raw_tag.tag_guid} is missing treatment amount')
            else:
                self.red = np.uint8(255)
                self.green = np.uint8(255)
                self.blue = np.uint8(255)
                self.treatment_what = ''
                self.additional_information = ''
                self.treatment_how_much_base_value = np.double(0.0)
                self.treatment_how_much_unit_exponent = np.int8(0)
                print(f'Tag {raw_tag.tag_guid} is an old-style tag - no treatment data')

            if file_id.tell() > end:
                print('File may be corrupted')
        else:
            raise ValueError('Encountered an error while loading '
                             f'WellInformation {raw_tag.tag_guid}')
