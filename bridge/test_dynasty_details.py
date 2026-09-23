"""Sanitized fixtures for the complete dynasty model and command."""
from contextlib import redirect_stdout, redirect_stderr
from dataclasses import replace
from io import StringIO
from pathlib import Path
import json
import tempfile
import unittest
from unittest.mock import patch, Mock

from bridge.dynasty_details import (
    DynastyDetails, SeasonContext, EnumValue, DepthSlot, PlayerHealth,
    RecruitingBoard, RecruitingTarget, next_games,
)
from bridge.models import Coach, Team, Player, RecordId, DynastySnapshot, ScheduleGame
from bridge.show_dynasty import display, export_dynasty, main
from bridge.load_dynasty import read_depth, read_health, read_recruiting, load_dynasty


def sample():
    player = Player(RecordId(10, 1), 'Sample', 'Player', 'QB', 80)
    roster = DynastySnapshot('save-hash', 'schema-hash',
        Coach(RecordId(11, 1), 'Sample', 'Coach', 7, True),
        Team(RecordId(12, 1), 7, 'Sample Team', (player,)))
    season = SeasonContext(2026, 0, 2, EnumValue(1, 'RegularSeason'), EnumValue(1, 'Season'))
    game = ScheduleGame(RecordId(13, 1), 0, 2, 'Sample Team', 'Opponent', 'Unplayed', None, None, True)
    health = PlayerHealth(player.record_id, EnumValue(1, 'Uninjured'), EnumValue(98, 'Unknown (98)'),
                          EnumValue(255, 'Unknown (255)'), 0, 0, 0, False)
    target = RecruitingTarget(RecordId(14, 1), RecordId(15, 1), RecordId(10, 2),
        'Sample Recruit', EnumValue(0, 'QB'), 20, 2, EnumValue(0, 'Open'), EnumValue(3, 'Offered'), 10)
    return DynastyDetails(roster, season, (game,), (DepthSlot('QB', 1, player.record_id),),
                          (health,), RecruitingBoard(RecordId(16, 1), 10, 0, 100, (target,)))


class NextGameTests(unittest.TestCase):
    def test_filters_past_other_season_completed_and_unscheduled(self):
        details = sample()
        game = details.schedule[0]
        games = (replace(game, week=4), replace(game, week=1),
                 replace(game, season_index=1), replace(game, status='HomeWon'),
                 replace(game, status='StatsReported'), replace(game, status='Unscheduled'), game)
        self.assertEqual(next_games(replace(details, schedule=games)), (game,))

    def test_retains_same_week_ambiguity(self):
        details = sample()
        second = replace(details.schedule[0], record_id=RecordId(13, 2))
        self.assertEqual(len(next_games(replace(details, schedule=(*details.schedule, second)))), 2)

    def test_empty_and_season_complete(self):
        details = sample()
        self.assertEqual(next_games(replace(details, schedule=())), ())
        self.assertEqual(next_games(replace(details, season=replace(details.season, week=10))), ())


class SectionReaderTests(unittest.TestCase):
    def depth_reader(self, values):
        reader = Mock()
        reader.pointer.return_value = 1
        reader.resolve.return_value = ({'name': 'DepthChart'}, 0)
        reader.schemas = {'DepthChart': [{'name': 'QB', 'type': 'Player[]'},
                                       {'name': 'GetPlayer', 'type': 'method'}]}
        reader.array.return_value = values
        return reader

    def test_depth_keeps_empty_slots_and_source_order(self):
        reader = self.depth_reader([None, (10 << 17) | 1])
        slots = read_depth(reader, {}, 0, sample().roster.team)
        self.assertEqual(slots, (DepthSlot('QB', 1, None), DepthSlot('QB', 2, RecordId(10, 1))))

    def test_depth_rejects_outside_roster_and_duplicates(self):
        for refs in ([10 << 17], [(10 << 17) | 1] * 2):
            with self.subTest(refs=refs), self.assertRaises(ValueError):
                read_depth(self.depth_reader(refs), {}, 0, sample().roster.team)

    def test_null_sections_are_unavailable(self):
        reader = Mock()
        reader.pointer.return_value = 0
        self.assertIsNone(read_depth(reader, {}, 0, sample().roster.team))
        self.assertIsNone(read_recruiting(reader, {}, 0))
        reader.resolve.assert_not_called()

    def test_health_preserves_unknown_enums_and_durations(self):
        reader = Mock()
        reader.resolve.return_value = ({'name': 'Player'}, 1)
        reader.field.side_effect = lambda info, row, key: {
            'InjuryStatus': 9, 'InjuryType': 88, 'InjurySeverity': 7,
            'MinInjuryDuration': 2, 'MaxInjuryDuration': 4,
            'TotalInjuryDuration': 6, 'IsInjuredReserve': True}[key]
        reader.label.side_effect = lambda info, name, value: f'Unknown ({value})'
        result = read_health(reader, sample().roster.team.players)[0]
        self.assertEqual(result.status, EnumValue(9, 'Unknown (9)'))
        self.assertEqual((result.min_duration, result.max_duration, result.total_duration), (2, 4, 6))
        self.assertTrue(result.injured_reserve)

    def recruiting_reader(self, refs):
        reader = Mock()
        reader.pointer.return_value = (16 << 17) | 1
        reader.array.return_value = refs
        reader.resolve.side_effect = lambda ref, name: ({'name': name}, 1)
        values = {'Recruit': (15 << 17) | 1, 'Player': (10 << 17) | 2,
                  'FirstName': 'Sample', 'LastName': 'Recruit', 'Position': 0,
                  'NationalRank': 20, 'PositionRank': 2, 'RecruitStage': 0,
                  'ScholarshipStatus': 3, 'ProspectHoursSpentCurrent': 10,
                  'RecruitingHoursAssigned': 10, 'RecruitingHoursProcessed': 0, 'RecruitingHoursTotal': 100}
        reader.field.side_effect = lambda info, row, name: values[name]
        reader.label.side_effect = lambda info, name, value: {'Position': 'QB', 'RecruitStage': 'Open', 'ScholarshipStatus': 'Offered'}[name]
        return reader

    def test_recruiting_follows_links_and_skips_empty_slots(self):
        reader = self.recruiting_reader([None, (14 << 17) | 1])
        self.assertEqual(read_recruiting(reader, {}, 0), sample().recruiting)

    def test_duplicate_recruits_rejected(self):
        reader = self.recruiting_reader([(14 << 17) | 1, (14 << 17) | 2])
        with self.assertRaisesRegex(ValueError, 'Duplicate recruit'):
            read_recruiting(reader, {}, 0)

    def test_empty_board_is_available(self):
        board = read_recruiting(self.recruiting_reader([]), {}, 0)
        self.assertEqual(board.targets, ())
        self.assertEqual(board.hours_total, 100)


class DynastyCommandTests(unittest.TestCase):
    def invoke(self, args, error=None):
        out, err = StringIO(), StringIO()
        code = 0
        with patch('sys.argv', ['show_dynasty', *args]), \
             patch('bridge.show_dynasty.load_dynasty', return_value=sample(), side_effect=error) as loader, \
             redirect_stdout(out), redirect_stderr(err):
            try:
                main()
            except SystemExit as failure:
                code = failure.code
        return code, out.getvalue(), err.getvalue(), loader

    def test_all_sections(self):
        code, out, err, loader = self.invoke(['save', 'schema', '--section', 'all'])
        self.assertEqual((code, err), (0, ''))
        loader.assert_called_once_with(Path('save'), Path('schema'))
        for text in ('Sample Team', 'Next scheduled: Week 2', 'Depth chart (source order)',
                     'duration units unverified', 'Sample Recruit', 'Unknown (98)'):
            self.assertIn(text, out)

    def test_unavailable_sections_and_no_next_game(self):
        out = StringIO()
        with redirect_stdout(out):
            display(replace(sample(), recruiting=None, depth_chart=None, schedule=()), 'all')
        self.assertIn('Recruiting board: unavailable', out.getvalue())
        self.assertIn('Depth chart: unavailable', out.getvalue())
        self.assertIn('No upcoming scheduled fixture', out.getvalue())

    def test_load_failures(self):
        for error in (OSError('missing'), ValueError('invalid')):
            with self.subTest(error=error):
                code, out, err, _ = self.invoke(['save', 'schema'], error)
                self.assertEqual((code, out), (1, ''))
                self.assertIn('Could not load dynasty:', err)

    def test_help_and_bad_args_do_not_load(self):
        for args, expected in ((['--help'], 0), ([], 2), (['s', 't', '--section', 'wrong'], 2)):
            with self.subTest(args=args):
                code, _, _, loader = self.invoke(args)
                self.assertEqual(code, expected)
                loader.assert_not_called()

    def test_export_complete_and_never_overwrites(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'dynasty.json'
            code, _, err, _ = self.invoke(['s', 't', '--export', str(path)])
            self.assertEqual((code, err), (0, ''))
            original = path.read_bytes()
            data = json.loads(original)
            self.assertEqual(data['format_version'], 1)
            self.assertEqual(len(data['dynasty']['recruiting']['targets']), 1)
            self.assertEqual(data['dynasty']['roster']['save_sha256'], 'save-hash')
            code, out, err, _ = self.invoke(['s', 't', '--export', str(path)])
            self.assertEqual((code, out), (1, ''))
            self.assertIn('Could not export dynasty:', err)
            self.assertEqual(path.read_bytes(), original)


class CompleteLoaderTests(unittest.TestCase):
    def test_captures_each_source_once_and_shares_frozen_bytes(self):
        details = sample()
        save, schema = Mock(), Mock()
        save.read_bytes.return_value = b'captured save'
        schema.read_bytes.return_value = b'captured schema'
        report = {'season_info': [{'CurrentSeasonYear': 2026, 'CurrentYear': 0,
                  'CurrentWeek': 2, 'CurrentWeekType': 1, 'CurrentWeekTypeLabel': 'RegularSeason',
                  'CurrentStage': 1, 'CurrentStageLabel': 'Season'}]}
        with patch('bridge.load_dynasty.DynastyReader') as reader, \
             patch('bridge.load_dynasty.inspect_fields') as fields, \
             patch('bridge.load_dynasty.inspect_schedule', return_value=report) as schedule, \
             patch('bridge.load_dynasty.snapshot_from_report', return_value=details.roster), \
             patch('bridge.load_dynasty.schedule_from_report', return_value=details.schedule), \
             patch('bridge.load_dynasty.read_depth', return_value=details.depth_chart), \
             patch('bridge.load_dynasty.read_health', return_value=details.health), \
             patch('bridge.load_dynasty.read_recruiting', return_value=details.recruiting):
            reader.return_value.resolve.return_value = ({}, 1)
            self.assertEqual(load_dynasty(save, schema), details)
            self.assertEqual(fields.call_args.args, schedule.call_args.args)
            captured_save, captured_schema = fields.call_args.args
            self.assertEqual(captured_save.read_bytes(), b'captured save')
            self.assertEqual(captured_schema.read_bytes(), b'captured schema')
        save.read_bytes.assert_called_once_with()
        schema.read_bytes.assert_called_once_with()

    def test_ambiguous_season_context_rejected(self):
        for contexts in ([], [{}, {}]):
            with self.subTest(contexts=contexts), \
                 patch('bridge.load_dynasty.DynastyReader'), \
                 patch('bridge.load_dynasty.inspect_fields'), \
                 patch('bridge.load_dynasty.snapshot_from_report', return_value=sample().roster), \
                 patch('bridge.load_dynasty.inspect_schedule', return_value={'season_info': contexts}):
                with self.assertRaisesRegex(ValueError, 'one linked season'):
                    load_dynasty(Mock(), Mock())


if __name__ == '__main__':
    unittest.main()
