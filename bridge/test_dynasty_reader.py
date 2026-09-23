"""Minimal binary fixtures exercise boundaries without distributing game data."""
import gzip
import json
import unittest
import zlib

from bridge.dynasty_reader import DynastyReader, FrozenSource


def bundle():
    return gzip.compress(json.dumps({'schemas': []}).encode())


def save_bytes(data=None):
    if data is None:
        data = bytearray(136)
        data[:4] = b'FrTk'
        data[4:8] = (128).to_bytes(4, 'big')
    chunk = zlib.compress(data)
    raw = bytearray(82)
    raw[:8] = b'FBCHUNKS'
    raw[74:78] = len(chunk).to_bytes(4, 'little')
    return bytes(raw) + chunk


class DynastyReaderTests(unittest.TestCase):
    def test_minimal_database_and_frozen_source(self):
        raw = save_bytes()
        reader = DynastyReader(raw, bundle())
        self.assertEqual(reader.tables, {})
        self.assertEqual(len(reader.save_sha256), 64)
        source = FrozenSource(raw)
        self.assertIs(source.read_bytes(), raw)
        self.assertIs(source.read_bytes(), raw)

    def test_bad_headers_and_chunk_bounds(self):
        for raw in (b'', b'X' * 82, save_bytes()[:-1], save_bytes()[:82]):
            with self.subTest(length=len(raw)), self.assertRaises(ValueError):
                DynastyReader(raw, bundle())

    def test_bad_compression_and_database_signature(self):
        raw = bytearray(save_bytes())
        raw[82:] = b'X' * (len(raw) - 82)
        for value in (bytes(raw), save_bytes(b'wrong database')):
            with self.subTest(value=value[:8]), self.assertRaises(ValueError):
                DynastyReader(value, bundle())

    def test_trailing_data_within_chunk_rejected(self):
        raw = bytearray(save_bytes() + b'x')
        raw[74:78] = (len(raw) - 82).to_bytes(4, 'little')
        with self.assertRaises(ValueError):
            DynastyReader(raw, bundle())

    def test_invalid_schema(self):
        for schema in (b'no gzip', gzip.compress(b'bad json'), gzip.compress(b'{}')):
            with self.subTest(schema=schema), self.assertRaises(ValueError):
                DynastyReader(save_bytes(), schema)

    def reference_reader(self):
        reader = DynastyReader(save_bytes(), bundle())
        reader.bases = {'UserRecruitTarget': 'RecruitTarget', 'CycleA': 'CycleB', 'CycleB': 'CycleA'}
        reader.tables = {10: {'id': 10, 'name': 'UserRecruitTarget', 'count': 3}}
        reader._empty = {10: {2}}
        return reader

    def test_reference_subtype_and_occupancy(self):
        reader = self.reference_reader()
        self.assertEqual(reader.resolve((10 << 17) | 1, 'RecruitTarget')[1], 1)
        for ref, expected in ((0, 'RecruitTarget'), (11 << 17, 'RecruitTarget'),
                              ((10 << 17) | 3, 'RecruitTarget'),
                              ((10 << 17) | 2, 'RecruitTarget'), (10 << 17, 'Player')):
            with self.subTest(ref=ref), self.assertRaises(ValueError):
                reader.resolve(ref, expected)
        self.assertFalse(reader.is_type('CycleA', 'Player'))

    def test_array_bounds_nulls_and_order(self):
        reader = self.reference_reader()
        array = {'id': 20, 'name': 'RecruitTarget[]', 'count': 1, 'words': 2,
                 'marker': 'ASTO', 'metadata': 0, 'records': 4}
        reader.tables[20] = array
        reader._empty[20] = set()
        values = [2, 0, (10 << 17) | 1]
        reader.data = b''.join(v.to_bytes(4, 'big') for v in values)
        self.assertEqual(reader.array(20 << 17, 'RecruitTarget', True), [None, (10 << 17) | 1])
        with self.assertRaises(ValueError):
            reader.array(20 << 17, 'RecruitTarget')
        reader.data = (3).to_bytes(4, 'big') + reader.data[4:]
        with self.assertRaisesRegex(ValueError, 'capacity'):
            reader.array(20 << 17, 'RecruitTarget', True)


if __name__ == '__main__':
    unittest.main()
