from enum import Enum

MAGIC_SEED = 0x10201


class Endianness(Enum):
    LITTLE_ENDIAN = 0
    BIG_ENDIAN = 1


def calculate(payload: bytes, init=0, sigbit=Endianness.LITTLE_ENDIAN):
    _crc, _y = init, 0

    for byte in payload:
        _x = byte
        _y = (_crc ^ _x) & 0x17
        _crc = (_crc >> 4) ^ (_y * MAGIC_SEED)
        _y = (_crc ^ (_x >> 4)) & 0x17
        _crc = (_crc >> 4) ^ (_y * MAGIC_SEED)

    if sigbit == Endianness.LITTLE_ENDIAN:
        return (_crc & 0xFF), ((_crc >> 8) & 0xFF)

    return ((_crc >> 8) & 0xFF), (_crc & 0xFF)


'''
fn crc16(msg: &[u8]) -> u16 {
    let mut crc: u16 = 0;
    let (mut c, mut q): (u16, u16);

    for byte in msg.iter() {
        c = *byte as u16;
        q = (crc ^ c) & 0o17;
        crc = (crc >> 4) ^ (q * 0o10201);
        q = (crc ^ (c >> 4)) & 0o17;
        crc = (crc >> 4) ^ (q * 0o10201);
    }

    crc
}
'''