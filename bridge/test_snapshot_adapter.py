import unittest

from bridge.snapshot_adapter import snapshot_from_report


class SnapshotAdapterTests(unittest.TestCase):
    def test_builds_snapshot_from_valid_report(self):
        # Use synthetic data so this test needs no game save or schema file.
        report = {
            "save_sha256": "sample-save-hash",
            "schema_sha256": "sample-schema-hash",
            "selection": {
                "status": "resolved",
                "team": {"table": 6351, "row": 2},
            },
            "roster_team_mismatches": [],
            "controlled_coaches": [
                {
                    "table": 4179,
                    "row": 10,
                    "FirstName": "Sample",
                    "LastName": "Coach",
                    "TeamIndex": 5,
                }
            ],
            "teams": [
                {
                    "table": 6351,
                    "row": 2,
                    "TeamIndex": 5,
                    "DisplayName": "Sample Team",
                    "players": [
                        {
                            "table": 4255,
                            "row": 10,
                            "FirstName": "Sample",
                            "LastName": "Player",
                            "PositionLabel": "QB",
                            "OverallRating": 85,
                        }
                    ],
                }
            ],
        }

        # Convert the report through the same adapter used by the application.
        snapshot = snapshot_from_report(report)

        # Verify the selected identities and roster values survived conversion.
        self.assertEqual(snapshot.coach.full_name, "Sample Coach")
        self.assertEqual(snapshot.team.name, "Sample Team")
        self.assertEqual(snapshot.team.record_id.row_id, 2)
        self.assertEqual(len(snapshot.team.players), 1)
        self.assertEqual(snapshot.team.players[0].full_name, "Sample Player")
        self.assertEqual(snapshot.team.players[0].position, "QB")
        self.assertEqual(snapshot.team.players[0].overall, 85)

    def test_rejects_unresolved_selection(self):
        # An unresolved selection must be rejected before any records are read.
        report = {
            "selection": {
                "status": "no_controlled_coach",
            },
        }

        # Check both the exception type and its explanation.
        with self.assertRaisesRegex(
            ValueError,
            "Cannot build snapshot: no_controlled_coach",
        ):
            snapshot_from_report(report)

    def test_rejects_roster_team_mismatches(self):
        # A resolved selection does not make inconsistent roster data acceptable.
        report = {
            "selection": {
                "status": "resolved",
            },
            "roster_team_mismatches": [
                {"player_row": 10},
            ],
        }

        # Reject the report before attempting to build team or player objects.
        with self.assertRaisesRegex(
            ValueError,
            "Cannot build snapshot: roster/team mismatches found",
        ):
            snapshot_from_report(report)

    def test_rejects_missing_selected_team(self):
        # The selection points to a team that is absent from the report.
        report = {
            "selection": {
                "status": "resolved",
                "team": {"table": 6351, "row": 2},
            },
            "roster_team_mismatches": [],
            "teams": [],
        }

        # A selection alone is not enough; its team record must exist.
        with self.assertRaisesRegex(
            ValueError,
            "Expected exactly one matching team record",
        ):
            snapshot_from_report(report)

    def test_rejects_duplicate_selected_team(self):
        # Two records claim the same source identity as the selected team.
        report = {
            "selection": {
                "status": "resolved",
                "team": {"table": 6351, "row": 2},
            },
            "roster_team_mismatches": [],
            "teams": [
                {"table": 6351, "row": 2},
                {"table": 6351, "row": 2},
            ],
        }

        # Reject ambiguous records before attempting to convert either one.
        with self.assertRaisesRegex(
            ValueError,
            "Expected exactly one matching team record",
        ):
            snapshot_from_report(report)

    def test_rejects_invalid_controlled_coach_count(self):
        # Check both a missing coach and multiple controlled coaches.
        for coaches in ([], [{}, {}]):
            with self.subTest(coach_count=len(coaches)):
                report = {
                    "selection": {
                        "status": "resolved",
                        "team": {"table": 6351, "row": 2},
                    },
                    "roster_team_mismatches": [],
                    "teams": [
                        {"table": 6351, "row": 2},
                    ],
                    "controlled_coaches": coaches,
                }

                # Reject the coach count before converting any records.
                with self.assertRaisesRegex(
                    ValueError,
                    "Expected exactly one controlled coach",
                ):
                    snapshot_from_report(report)

    def test_rejects_coach_team_index_mismatch(self):
        # The selected team uses index 5, but the coach belongs to index 6.
        report = {
            "selection": {
                "status": "resolved",
                "team": {"table": 6351, "row": 2},
            },
            "roster_team_mismatches": [],
            "teams": [
                {
                    "table": 6351,
                    "row": 2,
                    "TeamIndex": 5,
                    "DisplayName": "Sample Team",
                    "players": [],
                },
            ],
            "controlled_coaches": [
                {
                    "table": 4179,
                    "row": 10,
                    "FirstName": "Sample",
                    "LastName": "Coach",
                    "TeamIndex": 6,
                },
            ],
        }

        # Reject the conflicting relationship before returning a snapshot.
        with self.assertRaisesRegex(
            ValueError,
            "Coach and team indexes do not match",
        ):
            snapshot_from_report(report)

if __name__ == "__main__":
    unittest.main()