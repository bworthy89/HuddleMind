"""Independent examples for position summaries; no save files needed."""
import unittest

from bridge.models import Player, RecordId
from bridge.roster_summary import (
    average_overall_by_position,
    best_overall_by_position,
    count_players_by_position,
)


def roster(*entries):
    return tuple(Player(RecordId(1, i), 'Sample', str(i), position, rating)
                 for i, (position, rating) in enumerate(entries))


class RosterSummaryTests(unittest.TestCase):
    def test_empty_roster(self):
        for calculate in (count_players_by_position, best_overall_by_position,
                          average_overall_by_position):
            with self.subTest(calculate=calculate.__name__):
                self.assertEqual(calculate(()), {})

    def test_single_player_groups_including_zero_rating(self):
        players = roster(('QB', 0), ('WR', 85))
        self.assertEqual(count_players_by_position(players), {'QB': 1, 'WR': 1})
        self.assertEqual(best_overall_by_position(players), {'QB': 0, 'WR': 85})
        self.assertEqual(average_overall_by_position(players), {'QB': 0.0, 'WR': 85.0})

    def test_interleaved_groups_and_rating_ties(self):
        players = roster(('QB', 80), ('WR', 70), ('QB', 90), ('WR', 70), ('QB', 40))
        self.assertEqual(count_players_by_position(players), {'QB': 3, 'WR': 2})
        self.assertEqual(best_overall_by_position(players), {'QB': 90, 'WR': 70})
        self.assertEqual(average_overall_by_position(players), {'QB': 70.0, 'WR': 70.0})

    def test_average_is_not_rounded_by_calculation(self):
        result = average_overall_by_position(roster(('QB', 80), ('QB', 81), ('QB', 81)))
        self.assertAlmostEqual(result['QB'], 242 / 3)
        self.assertNotEqual(result['QB'], 80.7)

    def test_results_independent_of_roster_order(self):
        players = roster(('WR', 99), ('QB', 70), ('WR', 20), ('QB', 90))
        original = tuple((p.record_id, p.position, p.overall) for p in players)
        for calculate in (count_players_by_position, best_overall_by_position,
                          average_overall_by_position):
            with self.subTest(calculate=calculate.__name__):
                self.assertEqual(calculate(players), calculate(tuple(reversed(players))))
        self.assertEqual(tuple((p.record_id, p.position, p.overall) for p in players), original)


if __name__ == '__main__':
    unittest.main()
