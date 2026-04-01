import numpy as np

class CRC32:
    """
    Class for calculating CRC32s.

    For Quick Reference, see http://en.wikipedia.org/wiki/Cyclic_redundancy_check
    CRC32 implementation adapted from: http://damieng.com/blog/2006/08/08/calculating_crc32_in_c_and_net
    """
    DefaultSeed = 0xFFFFFFFF
    DefaultPolynomial = 0xEDB88320

    def __init__(self, polynomial=None, seed=None):
        if polynomial is None:
            polynomial = CRC32.DefaultPolynomial
        if seed is None:
            seed = CRC32.DefaultSeed

        self.polynomial = np.uint32(polynomial)
        self.seed = np.uint32(seed)
        self.table = CRC32.initialize_table(self.polynomial)
        self.hash = self.seed
        self.initialize()

    def initialize(self):
        self.hash = np.uint32(self.seed)

    def compute(self, bytes_, start=0, size=None):
        if size is None:
            size = len(bytes_) - start

        crc = CRC32.DefaultSeed ^ self.calculate_hash(self.table, self.seed, bytes_, start, size)
        return crc

    @staticmethod
    def initialize_table(polynomial):
        table = np.zeros((256,), dtype = np.uint32)
        polynomial = np.uint32(polynomial)

        for i, entry in enumerate(np.arange(0, 256, 1, np.uint32)):
            for _ in range(8):
                if entry & np.uint32(1) == np.uint32(1):
                    entry = (entry >> 1) ^ polynomial
                else:
                    entry >>= 1
            table[i] = entry

        return table

    @staticmethod
    def calculate_hash(table:np.ndarray[np.uint32], seed:np.uint32, buffer, start, size):
        crc = seed
        crcspace = range(start, start + size)
        for i in crcspace:
            lookup = np.uint8((buffer[i] ^ crc) & 0xFF)
            # in the matlab code they convert to uint16 here
            # but I think it is not necessary because of 0
            # indexing which avoids overflowing the np.uint8
            crc = (crc >> 8) ^ table[lookup]
        # chatgpt suggested crc & 0xFFFFFFFF
        # but I am not sure why this bitmasking would be necessary
        # in this case
        return crc
