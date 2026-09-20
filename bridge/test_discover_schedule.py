import unittest
from bridge.discover_schedule import enum_label


class ScheduleEnumTests(unittest.TestCase):
    def test_label_uses_value_and_excludes_aliases(self):
        field = {'enum': {'_members': [
            {'_name': 'First_', '_value': 3, '_index': 0},
            {'_name': 'AwayWon', '_value': 3, '_index': 1},
        ]}}
        self.assertEqual(enum_label(field, 3), 'AwayWon')
        self.assertEqual(enum_label(field, 1), 'Unknown (1)')

    def test_missing_or_ambiguous_enum_remains_unknown(self):
        self.assertEqual(enum_label({}, 0), 'Unknown (0)')
        self.assertEqual(enum_label({'enum': {'_members': [
            {'_name': 'One', '_value': 0}, {'_name': 'Two', '_value': 0},
        ]}}, 0), 'Unknown (0)')
