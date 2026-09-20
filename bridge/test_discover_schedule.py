import unittest
from bridge.discover_schedule import enum_label, result_label, schedule_references


class ScheduleEnumTests(unittest.TestCase):
    def test_completed_results_from_both_sides(self):
        for status, home, away, is_home, expected in [
            ('HomeWon', 21, 7, True, 'win'), ('HomeWon', 21, 7, False, 'loss'),
            ('AwayWon', 7, 21, True, 'loss'), ('AwayWon', 7, 21, False, 'win'),
            ('Tied', 7, 7, True, 'tie'),
        ]:
            with self.subTest(status=status, is_home=is_home):
                self.assertEqual(result_label(status, home, away, is_home), expected)

    def test_scores_do_not_imply_completion(self):
        self.assertEqual(result_label('Unplayed', 21, 7, True), 'pending')
        self.assertEqual(result_label('StatsReported', 21, 7, True), 'unknown')
        self.assertEqual(result_label('Unknown (15)', 0, 0, True), 'unknown')

    def test_contradictory_completed_scores_rejected(self):
        for status, home, away in [('HomeWon', 0, 7), ('AwayWon', 7, 7), ('Tied', 7, 0)]:
            with self.subTest(status=status), self.assertRaises(ValueError):
                result_label(status, home, away, True)

    def test_schedule_reference_validation(self):
        data = bytearray(180)
        def put(offset, value):
            data[offset:offset + 4] = value.to_bytes(4, 'big')
        put(60, 1)  # Array free-list sentinel.
        put(64, 2)  # Two game references.
        put(68, 2 << 17)
        put(72, (2 << 17) + 1)
        put(156, 2)  # Game free-list sentinel.
        tables = {
            1: dict(id=1, name='SeasonGame[]', metadata=64, records=68, count=1, words=2),
            2: dict(id=2, name='SeasonGame', metadata=160, records=160, count=2, words=1),
        }
        self.assertEqual(schedule_references(data, tables, 1 << 17), {(2, 0), (2, 1)})
        for offset, value in [(64, 3), (72, 2 << 17), (72, 0), (72, 3 << 17), (72, (2 << 17) + 2)]:
            changed = data.copy()
            changed[offset:offset + 4] = value.to_bytes(4, 'big')
            with self.subTest(offset=offset, value=value), self.assertRaises(ValueError):
                schedule_references(changed, tables, 1 << 17)

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
