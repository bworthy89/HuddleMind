"""Local event construction and serialization; no network access."""
from dataclasses import replace
from pathlib import Path
import json
import tempfile
import unittest
from uuid import UUID

from bridge.local_store import initialize_database, create_dynasty, save_observation, list_observations
from bridge.sync_event import build_observation_event, serialize_observation_event
from bridge.test_dynasty_details import sample


class SyncEventTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.path = Path(folder.name) / 'history.sqlite3'
        initialize_database(self.path)
        self.dynasty = create_dynasty(self.path, 'Sample')
        self.identity = save_observation(self.path, self.dynasty, sample())

    def test_original_timestamp_payload_and_fresh_uuid(self):
        before = self.path.read_bytes()
        event = build_observation_event(self.path, self.dynasty, self.identity)
        self.assertEqual(UUID(event.event_id).version, 4)
        self.assertEqual(event.observed_at, list_observations(self.path, self.dynasty)[0][1])
        decoded = json.loads(serialize_observation_event(event))
        self.assertEqual(decoded['payload']['roster']['team']['name'], 'Sample Team')
        self.assertEqual(decoded['event_id'], event.event_id)
        self.assertEqual(decoded['schema_version'], 1)
        self.assertEqual(decoded['event_type'], 'dynasty.observation.captured')
        self.assertNotEqual(build_observation_event(self.path, self.dynasty, self.identity).event_id, event.event_id)
        self.assertEqual(self.path.read_bytes(), before)

    def test_wrong_dynasty_and_missing_observation_rejected(self):
        for dynasty, identity in (('other', self.identity), (self.dynasty, 999)):
            with self.subTest(dynasty=dynasty), self.assertRaises(ValueError):
                build_observation_event(self.path, dynasty, identity)

    def test_serialization_preserves_unicode_and_rejects_nonfinite_numbers(self):
        event = build_observation_event(self.path, self.dynasty, self.identity)
        serialized = serialize_observation_event(replace(event, payload={'name': '日本語'}))
        self.assertIn('日本語', serialized)
        for value in (float('nan'), float('inf'), float('-inf')):
            with self.subTest(value=value), self.assertRaises(ValueError):
                serialize_observation_event(replace(event, payload={'value': value}))


if __name__ == '__main__':
    unittest.main()
