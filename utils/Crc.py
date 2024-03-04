from enum import Enum
from ctypes import c_ushort
from error_handler import NoSasConnection, BadCRC

MAGIC_SEED = 0x8408
table = []


class Endianness(Enum):
    LITTLE_ENDIAN = 0
    BIG_ENDIAN = 1


for i in range(0, 256):
    val = c_ushort(i).value
    for j in range(0, 8):
        val = c_ushort(val >> 1).value ^ MAGIC_SEED if val & 0x0001 else c_ushort(val >> 1).value
    table.append(hex(val))


def calculate(payload=None, init=0, sigbit=Endianness.LITTLE_ENDIAN):
    _crc = init

    for c in payload:
        q = _crc ^ c
        _crc = c_ushort(_crc >> 8).value ^ int(table[(q & 0x00ff)], 0)

    if sigbit == Endianness.BIG_ENDIAN:
        _crc = (_crc & 0x00ff) << 8 | (_crc & 0xff00) >> 8
    else:
        _crc = (_crc & 0xff00) >> 8 | (_crc & 0x00ff) << 8

    return [((_crc >> 8) & 0xFF), (_crc & 0xFF)]

def validate(check=None, init=0, sigbit=Endianness.LITTLE_ENDIAN):
    """Function in charge of the CRC Check"""
    if check == "":
        raise NoSasConnection

    rcvd_crc = [int.from_bytes(check[-2:-1]), int.from_bytes(check[-1:])]
    my_crc = calculate(check[0:-2], init=init, sigbit=sigbit)

    if rcvd_crc != my_crc:
        raise BadCRC(hex(check))
    else:
        return check[1:-2]


''' Tableless algo in Python and Rust
def calculate(payload: bytes, init=0, sigbit=Endianness.LITTLE_ENDIAN):
    crc, y = init, 0

    for byte in payload:
        x = c_ushort(byte)
        y = (crc ^ int(x)) & 0o17
        crc = (crc >> 8) ^ (y * MAGIC_SEED)
        y = (crc ^ (x >> 8)) & 0o17
        crc = (crc >> 8) ^ (y * MAGIC_SEED)

    if sigbit == Endianness.BIG_ENDIAN:
        return crc & 0xFF, (crc >> 8) & 0xFF

    return (crc >> 8) & 0xFF, crc & 0xFF

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