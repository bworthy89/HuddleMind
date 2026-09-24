"""Independent examples for position summaries; no save files needed."""
import unittest

from bridge.models import Player, PlayerRating, RecordId
from bridge.roster_summary import (
    average_overall_by_position,
    best_overall_by_position,
    count_players_by_position,
    get_player_rating,
    average_rating_by_position,
    count_available_ratings_by_position,
    summarize_rating_by_position,
    rank_players_by_position,
    summarize_position_depth,
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


class IndividualRatingSummaryTests(unittest.TestCase):
    def setUp(self):
        # Mix absent fields, explicit None, and zero so missing data cannot
        # accidentally become a zero or contribute to the denominator.
        self.players = tuple(
            Player(RecordId(1, row), 'Sample', str(row), position, 80, ratings)
            for row, (position, ratings) in enumerate([
                ('WR', ()),
                ('QB', (PlayerRating('StrengthRating', 99), PlayerRating('SpeedRating', 90))),
                ('QB', (PlayerRating('SpeedRating', 0),)),
                ('QB', ()),
                ('QB', (PlayerRating('SpeedRating', None),)),
                ('C', (PlayerRating('SpeedRating', 0),)),
            ])
        )

    def test_lookup_selects_exact_field_and_preserves_zero_and_missing(self):
        self.assertEqual(get_player_rating(self.players[1], 'SpeedRating'), 90)
        self.assertEqual(get_player_rating(self.players[2], 'SpeedRating'), 0)
        for player, field in ((self.players[0], 'SpeedRating'),
                              (self.players[4], 'SpeedRating'),
                              (self.players[1], 'speedrating')):
            with self.subTest(player=player.record_id, field=field):
                self.assertIsNone(get_player_rating(player, field))

    def test_average_excludes_missing_but_includes_zero(self):
        self.assertEqual(average_rating_by_position(self.players, 'SpeedRating'),
                         {'QB': 45.0, 'C': 0.0})

    def test_coverage_includes_positions_without_available_ratings(self):
        self.assertEqual(count_available_ratings_by_position(self.players, 'SpeedRating'),
                         {'WR': 0, 'QB': 2, 'C': 1})

    def test_summary_reports_sorted_positions_and_complete_coverage(self):
        result = summarize_rating_by_position(self.players, 'SpeedRating')
        self.assertEqual(list(result), ['C', 'QB', 'WR'])
        self.assertEqual(result, {
            'C': {'roster_count': 1, 'rated_players': 1, 'average': 0.0},
            'QB': {'roster_count': 4, 'rated_players': 2, 'average': 45.0},
            'WR': {'roster_count': 1, 'rated_players': 0, 'average': None},
        })

    def test_empty_roster_and_entirely_missing_field(self):
        for calculate in (average_rating_by_position, count_available_ratings_by_position,
                          summarize_rating_by_position):
            with self.subTest(helper=calculate.__name__):
                self.assertEqual(calculate((), 'SpeedRating'), {})
        self.assertEqual(average_rating_by_position(self.players, 'ThrowPowerRating'), {})
        result = summarize_rating_by_position(self.players, 'ThrowPowerRating')
        self.assertTrue(all(row['average'] is None and row['rated_players'] == 0
                            for row in result.values()))

    def test_average_retains_precision(self):
        players = tuple(Player(RecordId(1, i), 'Sample', str(i), 'QB', 80,
                               (PlayerRating('SpeedRating', value),))
                        for i, value in enumerate((80, 81, 81)))
        self.assertAlmostEqual(average_rating_by_position(players, 'SpeedRating')['QB'], 242 / 3)

    def test_results_do_not_depend_on_order_or_mutate_players(self):
        original = repr(self.players)
        for calculate in (average_rating_by_position, count_available_ratings_by_position,
                          summarize_rating_by_position):
            with self.subTest(helper=calculate.__name__):
                self.assertEqual(calculate(self.players, 'SpeedRating'),
                                 calculate(tuple(reversed(self.players)), 'SpeedRating'))
        self.assertEqual(repr(self.players), original)


class PositionDepthTests(unittest.TestCase):
    def test_empty_roster(self):
        self.assertEqual(rank_players_by_position(()), {})
        self.assertEqual(summarize_position_depth(()), {})

    def test_top_two_gap_ties_and_single_player_zero(self):
        players = roster(('QB', 70), ('WR', 80), ('QB', 90),
                         ('WR', 80), ('QB', 85), ('K', 0))
        self.assertEqual(summarize_position_depth(players), {
            'K': {'roster_count': 1, 'top_overall': 0, 'next_overall': None, 'gap': None},
            'QB': {'roster_count': 3, 'top_overall': 90, 'next_overall': 85, 'gap': 5},
            'WR': {'roster_count': 2, 'top_overall': 80, 'next_overall': 80, 'gap': 0},
        })

    def test_second_player_zero_is_available(self):
        result = summarize_position_depth(roster(('QB', 0), ('QB', 75)))['QB']
        self.assertEqual(result['next_overall'], 0)
        self.assertEqual(result['gap'], 75)

    def test_ranking_ties_use_name_then_full_record_identity(self):
        # Case-insensitive name ties must resolve the same way after reordering.
        players = (
            Player(RecordId(2, 0), 'Alex', 'Sample', 'QB', 80),
            Player(RecordId(1, 5), 'alex', 'Sample', 'QB', 80),
            Player(RecordId(1, 3), 'Alex', 'Sample', 'QB', 80),
            Player(RecordId(1, 1), 'Zoe', 'Sample', 'QB', 80),
            Player(RecordId(1, 8), 'Top', 'Sample', 'QB', 90),
            Player(RecordId(3, 0), 'Other', 'Sample', 'C', 70),
        )
        original = repr(players)
        ranked = rank_players_by_position(players)
        self.assertEqual(list(ranked), ['C', 'QB'])
        self.assertIsInstance(ranked['QB'], tuple)
        self.assertEqual([p.record_id for p in ranked['QB']],
                         [RecordId(1, 8), RecordId(1, 3), RecordId(1, 5),
                          RecordId(2, 0), RecordId(1, 1)])
        self.assertEqual(ranked, rank_players_by_position(tuple(reversed(players))))
        self.assertEqual(summarize_position_depth(players),
                         summarize_position_depth(tuple(reversed(players))))
        self.assertEqual(repr(players), original)


if __name__ == '__main__':
    unittest.main()
