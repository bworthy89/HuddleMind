import unittest
from bridge.discover_rosters import table_directory


def fixture():
    data = bytearray(128 + 236 + 8)
    def put(offset, value):
        data[offset:offset + 4] = value.to_bytes(4, 'big')
    data[:4] = b'FrTk'
    put(4, 128)
    put(20, 1)
    start = 128
    put(start + 128, 4096)
    data[start + 148:start + 152] = b'SPBF'
    header = start + 168
    put(header + 4, 4096)
    put(header + 16, 36)
    data[header + 32:header + 36] = b'BSFT'
    put(header + 36, 36)
    put(header + 40, 36)
    put(header + 52, 1)
    return data


class DirectoryTests(unittest.TestCase):
    def test_exact_boundary(self):
        self.assertEqual(list(table_directory(fixture())), [4096])

    def test_trailer_and_lengths(self):
        for offset in (4, 20, 128 + 168 + 40, len(fixture()) - 1):
            data = fixture()
            data[offset] = 255
            with self.assertRaises(ValueError):
                table_directory(data)

    def test_record_marker_is_not_scanned(self):
        data = fixture()
        data[128:132] = b'SPBF'
        self.assertEqual(len(table_directory(data)), 1)
