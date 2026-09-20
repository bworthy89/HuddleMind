import unittest
from bridge.discover_fields import empty_rows, layout, packed_value, controlled_selection


class PackedFieldTests(unittest.TestCase):
    def test_selection_outcomes(self):
        self.assertEqual(controlled_selection([])['status'], 'no_controlled_coach')
        self.assertEqual(controlled_selection([{}, {}])['status'], 'multiple_controlled_coaches')
        for candidates, expected in [([], 'missing_team'), ([{}, {}], 'ambiguous_team'), ([{}], 'resolved')]:
            self.assertEqual(controlled_selection([{'team_candidates': candidates}])['status'], expected)

    def test_reversed_packing(self):
        data = (0).to_bytes(4, 'big') + (8).to_bytes(4, 'big') + bytes.fromhex('123456ab')
        info = dict(fields=2, metadata=0, words=1, records=8, count=1)
        fields = layout(data, info, [dict(name='small', type='int'), dict(name='large', type='int')])
        self.assertEqual(packed_value(data, info, fields, 0, 'small'), 0xab)
        self.assertEqual(packed_value(data, info, fields, 0, 'large'), 0x123456)
        with self.assertRaises(ValueError):
            packed_value(data, info, fields, 1, 'small')

    def test_free_list_and_cycle(self):
        data = bytearray(76)
        data[48:52] = (3).to_bytes(4, 'big')
        data[60:64] = (1).to_bytes(4, 'big')
        data[68:72] = (3).to_bytes(4, 'big')
        info = dict(metadata=64, records=64, words=1, count=3)
        self.assertEqual(empty_rows(data, info), {1})
        data[68:72] = (1).to_bytes(4, 'big')
        with self.assertRaises(ValueError):
            empty_rows(data, info)
        data[68:72] = (4).to_bytes(4, 'big')
        with self.assertRaises(ValueError):
            empty_rows(data, info)

    def test_layout_gap_rejected(self):
        with self.assertRaises(ValueError):
            layout((8).to_bytes(4, 'big'), dict(metadata=0, fields=1, words=1), [dict(name='bad', type='int')])
