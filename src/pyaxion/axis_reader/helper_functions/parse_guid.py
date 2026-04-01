def parse_guid(guidBytes):
    """Parse a Microsoft encoded GUID from bytes"""
    guid_str = "%02x%02x%02x%02x-%02x%02x-%02x%02x-%02x%02x-%02x%02x%02x%02x%02x%02x" % (
        guidBytes[3], guidBytes[2], guidBytes[1], guidBytes[0],
        guidBytes[5], guidBytes[4],
        guidBytes[7], guidBytes[6],
        guidBytes[8], guidBytes[9],
        guidBytes[10], guidBytes[11], guidBytes[12], guidBytes[13], guidBytes[14], guidBytes[15]
    )
    return guid_str.replace(' ', '0')

def encode_guid(guidStr:str) -> bytes:
    """Encode a Microsoft encoded GUID from string"""
    guidStr = guidStr.replace('-', '').lower()
    if len(guidStr) != 32:
        raise ValueError("GUID string must be 32 characters long")

    guid_bytes = bytearray(16)
    guid_bytes[0] = int(guidStr[6:8], 16)
    guid_bytes[1] = int(guidStr[4:6], 16)
    guid_bytes[2] = int(guidStr[2:4], 16)
    guid_bytes[3] = int(guidStr[0:2], 16)

    guid_bytes[4] = int(guidStr[10:12], 16)
    guid_bytes[5] = int(guidStr[8:10], 16)

    guid_bytes[6] = int(guidStr[14:16], 16)
    guid_bytes[7] = int(guidStr[12:14], 16)

    for i in range(8, 16):
        guid_bytes[i] = int(guidStr[i * 2:i * 2 + 2], 16)

    return bytes(guid_bytes)
