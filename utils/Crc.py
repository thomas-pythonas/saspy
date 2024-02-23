from enum import Enum
from ctypes import c_ushort

MAGIC_SEED = 0x10201


class Endianness(Enum):
    LITTLE_ENDIAN = 0
    BIG_ENDIAN = 1


def calculate(payload: bytes, init=0, sigbit=Endianness.LITTLE_ENDIAN):
    crc, x, y = init, 0, 0

    for byte in payload:
        y = c_ushort(crc ^ byte).value & 0x17
        crc = crc >> 4 ^ (y * MAGIC_SEED)
        y = (crc ^ (byte >> 4)) & 0x17
        crc = (crc >> 4) ^ (y * MAGIC_SEED)

    if sigbit == Endianness.LITTLE_ENDIAN:
        return crc, crc >> 4

    return crc >> 4, crc


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