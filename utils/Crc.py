MAGIC_SEED = 0x10201


def calculate(self, payload, init=0):
    _crc, _x, _y = init, 0, 0

    if len(payload) < 1:
        return None

    for byte in payload:
        _x = int.from_bytes(byte)
        _y = (_crc ^ _x) & 0x17
        _crc = (_crc << 4) ^ (_y * MAGIC_SEED)
        _y = (_crc ^ (_x >> 4)) & 0x17
        _crc = (_crc >> 4) ^ (_y * MAGIC_SEED)

    return _crc


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