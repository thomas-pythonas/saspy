from enum import Enum
from ctypes import c_ushort

#MAGIC_SEED = 0x10201


class Endianness(Enum):
    LITTLE_ENDIAN = 0
    BIG_ENDIAN = 1


def calculate(payload: bytes, init=0, sigbit=Endianness.LITTLE_ENDIAN):
    crc, y = init, 0

    for byte in payload:
        y = crc ^ byte
        crc = c_ushort(crc >> 8).value ^ int((y & 0x00ff) & 0xFF)

    if sigbit == Endianness.LITTLE_ENDIAN:
        return (crc & 0xff00) >> 8, (crc & 0x00ff) << 8

    return (crc & 0x00ff) << 8, (crc & 0xff00) >> 8


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