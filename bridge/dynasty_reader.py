"""Read one immutable save/schema pair; never write to game files."""
import gzip
import hashlib
import json
import zlib

from bridge.discover_fields import layout, packed_value
from bridge.discover_rosters import empty_rows, table_directory, u32, word_field
from bridge.discover_schedule import enum_label


class FrozenSource:
    """Let existing discovery functions reuse bytes captured once from disk."""
    def __init__(self, data):
        self.data = data

    def read_bytes(self):
        return self.data


class DynastyReader:
    def __init__(self, save_bytes, schema_bytes):
        if len(save_bytes) < 82 or save_bytes[:8] != b'FBCHUNKS':
            raise ValueError('Not a supported save header')
        size = int.from_bytes(save_bytes[74:78], 'little')
        if size <= 0 or size > len(save_bytes) - 82:
            raise ValueError('Invalid compressed chunk bounds')
        decoder = zlib.decompressobj()
        try:
            self.data = decoder.decompress(save_bytes[82:82 + size], 64 * 1024 * 1024)
        except zlib.error as error:
            raise ValueError('Invalid compressed database') from error
        if not decoder.eof or decoder.unused_data or decoder.unconsumed_tail:
            raise ValueError('Incomplete or oversized compressed database')
        try:
            bundle = json.loads(gzip.decompress(schema_bytes))
            self.schemas = {s['name']: s['attributes'] for s in bundle['schemas']}
            self.bases = {s['name']: s.get('base') for s in bundle['schemas']}
        except (OSError, EOFError, ValueError, KeyError, TypeError) as error:
            raise ValueError('Invalid schema bundle') from error
        self.tables = {key: items[0] for key, items in table_directory(self.data).items()}
        self._empty = {}
        self._layouts = {}
        self.save_sha256 = hashlib.sha256(save_bytes).hexdigest()
        self.schema_sha256 = hashlib.sha256(schema_bytes).hexdigest()

    def resolve(self, reference, expected):
        table_id, row = divmod(reference, 1 << 17)
        info = self.tables.get(table_id)
        if not reference or info is None or not self.is_type(info['name'], expected) or row >= info['count']:
            raise ValueError(f'Invalid {expected} reference')
        if table_id not in self._empty:
            self._empty[table_id] = empty_rows(self.data, info)
        if row in self._empty[table_id]:
            raise ValueError(f'Unused {expected} reference')
        return info, row

    def is_type(self, actual, expected):
        # Accept only inheritance explicitly recorded in this schema bundle.
        seen = set()
        while actual and actual not in seen:
            if actual == expected:
                return True
            seen.add(actual)
            actual = self.bases.get(actual)
        return False

    def field(self, info, row, name):
        attributes = self.schemas[info['name']]
        attribute = next((a for a in attributes if a['name'] == name), None)
        if attribute is None:
            raise ValueError(f"Missing schema field {info['name']}.{name}")
        if attribute['type'] == 'string':
            return word_field(self.data, info, attributes, row, name)
        if info['id'] not in self._layouts:
            self._layouts[info['id']] = layout(self.data, info, attributes)
        return packed_value(self.data, info, self._layouts[info['id']], row, name)

    def pointer(self, info, row, name):
        # Method-bearing schemas may not support general packing; isolated
        # reference words can still be checked without guessing other fields.
        return word_field(self.data, info, self.schemas[info['name']], row, name)

    def label(self, info, name, value):
        attribute = next(a for a in self.schemas[info['name']] if a['name'] == name)
        return enum_label(attribute, value)

    def array(self, reference, expected, allow_null=False):
        info, row = self.resolve(reference, expected + '[]')
        if info['marker'] != 'ASTO':
            raise ValueError('Expected an array table')
        length = u32(self.data, info['metadata'] + row * 4)
        if length > info['words']:
            raise ValueError('Array length exceeds row capacity')
        result = []
        for index in range(length):
            value = u32(self.data, info['records'] + (row * info['words'] + index) * 4)
            if value == 0 and allow_null:
                result.append(None)
            else:
                self.resolve(value, expected)
                result.append(value)
        return result
