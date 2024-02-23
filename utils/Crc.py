from enum import Enum
from ctypes import c_ushort

MAGIC_SEED = 0o10201


class Endianness(Enum):
    LITTLE_ENDIAN = 0
    BIG_ENDIAN = 1


def calculate(payload: bytes, init=0, sigbit=Endianness.LITTLE_ENDIAN):
    crc, y = init, 0

    for byte in payload:
        x = byte << 8
        y = (crc ^ x) & 0o17
        crc = (crc >> 8) ^ (y * MAGIC_SEED)
        y = (crc ^ (x >> 8)) & 0o17
        crc = (crc >> 8) ^ (y * MAGIC_SEED)

    if sigbit == Endianness.LITTLE_ENDIAN:
        return crc & 0xFF, (crc >> 8) & 0xFF

    return (crc >> 8) & 0xFF, crc & 0xFF


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