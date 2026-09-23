"""Check controlled-team results with synthetic games; no save files needed."""
from dataclasses import replace
import unittest

from bridge.models import RecordId, ScheduleGame
from bridge.schedule_summary import summarize_results


def game(status, home=True):
    return ScheduleGame(RecordId(10, 1), 0, 1, 'Home', 'Away', status, None, None, home)


class ScheduleSummaryTests(unittest.TestCase):
    def test_wins_and_losses_from_either_side(self):
        for status, home, outcome in (
            ('HomeWon', True, 'wins'), ('HomeWon', False, 'losses'),
            ('AwayWon', True, 'losses'), ('AwayWon', False, 'wins'),
        ):
            with self.subTest(status=status, home=home):
                result = summarize_results((game(status, home),))
                self.assertEqual(result[outcome], 1)
                self.assertEqual(sum(result.values()), 1)

    def test_zero_score_ties_from_either_side(self):
        for home in (True, False):
            with self.subTest(home=home):
                result = summarize_results((replace(game('Tied', home), home_score=0, away_score=0),))
                self.assertEqual(result, dict(wins=0, losses=0, ties=1, pending=0, unknown=0))

    def test_pending_statuses_do_not_become_results_from_scores(self):
        for status in ('Unscheduled', 'Unplayed', 'HomeScheduled', 'AwayScheduled'):
            with self.subTest(status=status):
                result = summarize_results((replace(game(status), home_score=28, away_score=7),))
                self.assertEqual(result, dict(wins=0, losses=0, ties=0, pending=1, unknown=0))

    def test_unknown_statuses_remain_unknown(self):
        for status in ('StatsReported', 'Unknown (15)', 'FutureStatus'):
            with self.subTest(status=status):
                result = summarize_results((game(status),))
                self.assertEqual(result, dict(wins=0, losses=0, ties=0, pending=0, unknown=1))

    def test_empty_and_independent_calls(self):
        first = summarize_results(())
        self.assertEqual(first, dict(wins=0, losses=0, ties=0, pending=0, unknown=0))
        first['wins'] = 99
        self.assertEqual(summarize_results(())['wins'], 0)

    def test_mixed_schedule_counts_every_game_once(self):
        games = (game('AwayWon', False), game('HomeWon', False), game('Tied'),
                 game('Unplayed'), game('HomeScheduled'), game('StatsReported'))
        before = tuple(games)
        result = summarize_results(games)
        self.assertEqual(result, dict(wins=1, losses=1, ties=1, pending=2, unknown=1))
        self.assertEqual(sum(result.values()), len(games))
        self.assertEqual(games, before)


if __name__ == '__main__':
    unittest.main()
