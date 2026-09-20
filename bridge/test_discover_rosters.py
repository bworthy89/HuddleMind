"""Synthetic boundary checks; no game assets are needed."""
import unittest

from bridge.discover_rosters import table, u32, word_field


class RosterProbeTests(unittest.TestCase):
    def test_integer_bounds(self):
        for offset in (-1, 1, 4):
            with self.assertRaises(ValueError):
                u32(b"\0" * 4, offset)

    def test_truncated_header(self):
        with self.assertRaises(ValueError):
            table(b"SPBF", 0)

    def fixture(self):
        # One descriptor, one string pointer, and a bounded string section.
        data = b"\0" * 8 + b"Ada\0"
        info = dict(count=1, fields=1, metadata=0, records=4, words=1,
                    strings=8, string_end=12)
        attrs = [dict(name="Name", type="string", maxLength="4")]
        return data, info, attrs

    def test_string_pointer_and_row_bounds(self):
        data, info, attrs = self.fixture()
        self.assertEqual(word_field(data, info, attrs, 0, "Name"), "Ada")
        for row in (-1, 1):
            with self.assertRaises(ValueError):
                word_field(data, info, attrs, row, "Name")
        data = data[:4] + (4).to_bytes(4, "big") + data[8:]
        with self.assertRaises(ValueError):
            word_field(data, info, attrs, 0, "Name")

    def test_packed_field_rejected(self):
        data, info, attrs = self.fixture()
        data = (1).to_bytes(4, "big") + data[4:]
        with self.assertRaises(ValueError):
            word_field(data, info, attrs, 0, "Name")


if __name__ == "__main__":
    unittest.main()
