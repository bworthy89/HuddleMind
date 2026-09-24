"""Exercise the receiver over real loopback HTTP using synthetic events."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from dataclasses import asdict
from http.client import HTTPConnection
import json
from pathlib import Path
import sqlite3
import tempfile
from threading import Thread
import unittest
from unittest.mock import patch
from uuid import uuid4

from bridge.receive_api import create_server, MAX_BODY
from bridge.receiver_store import APPLICATION_ID, initialize_receiver, store_event
from bridge.validate_event import decode_event
from bridge.test_dynasty_details import sample


def valid_event():
    payload = asdict(sample())
    payload['roster']['save_sha256'] = 'a' * 64
    payload['roster']['schema_sha256'] = 'b' * 64
    return dict(schema_version=1, event_type='dynasty.observation.captured',
                event_id=str(uuid4()), dynasty_id=str(uuid4()),
                observed_at='2026-09-23T18:00:00+00:00', payload=payload)


class ReceiverTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name) / 'receiver.sqlite3'
        self.event = valid_event()
        self.token = 'synthetic-test-token-' + 'x' * 32
        self.start()

    def start(self):
        self.server = create_server(self.path, self.token, 'test-owner', [self.event['dynasty_id']], 0)
        self.thread = Thread(target=self.server.serve_forever, kwargs={'poll_interval': 0.01}, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)

    def post(self, event=None, body=None, headers=None, path='/v1/observations', method='POST'):
        if body is None:
            body = json.dumps(event if event is not None else self.event).encode('utf-8')
        settings = {'Authorization': 'Bearer ' + self.token, 'Content-Type': 'application/json'}
        if headers:
            settings.update(headers)
        client = HTTPConnection('127.0.0.1', self.server.server_port, timeout=10)
        try:
            client.request(method, path, body=body, headers=settings)
            response = client.getresponse()
            return response.status, json.loads(response.read())
        finally:
            client.close()

    def rows(self):
        connection = sqlite3.connect(self.path)
        try:
            return connection.execute('SELECT * FROM received_events').fetchall()
        finally:
            connection.close()

    def test_first_delivery_and_duplicate_commit_once(self):
        self.assertEqual(self.post(), (201, {'event_id': self.event['event_id'], 'status': 'stored'}))
        before = self.rows()
        self.assertEqual(self.post(body=json.dumps(self.event, indent=4, sort_keys=True).encode()),
                         (200, {'event_id': self.event['event_id'], 'status': 'already_stored'}))
        self.assertEqual(self.rows(), before)
        self.assertEqual(len(before), 1)

    def test_restart_preserves_duplicate_acknowledgment(self):
        self.post()
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.start()
        self.assertEqual(self.post()[1]['status'], 'already_stored')

    def test_conflict_does_not_overwrite_original(self):
        self.post()
        before = self.rows()
        changed = deepcopy(self.event)
        changed['payload']['roster']['team']['name'] = 'Changed Team'
        self.assertEqual(self.post(changed)[0], 409)
        self.assertEqual(self.rows(), before)

    def test_concurrent_retries_store_once(self):
        with ThreadPoolExecutor(max_workers=4) as workers:
            results = list(workers.map(lambda _: self.post(), range(4)))
        self.assertEqual(sorted(status for status, _ in results), [200, 200, 200, 201])
        self.assertEqual(len(self.rows()), 1)

    def test_authentication_and_dynasty_authorization(self):
        self.assertEqual(self.post(headers={'Authorization': ''})[0], 401)
        self.assertEqual(self.post(headers={'Authorization': 'Bearer wrong'})[0], 401)
        changed = deepcopy(self.event)
        changed['dynasty_id'] = str(uuid4())
        self.assertEqual(self.post(changed)[0], 403)
        self.assertEqual(self.rows(), [])

    def test_invalid_envelopes_and_nested_data_rejected(self):
        cases = []
        for name, value in (('schema_version', 2), ('schema_version', True), ('event_id', 'bad'),
                            ('observed_at', '2026-09-23T18:00:00'), ('event_type', 'other'), ('payload', {})):
            changed = deepcopy(self.event)
            changed[name] = value
            cases.append(changed)
        changed = deepcopy(self.event)
        changed['payload']['roster']['team']['players'][0]['overall'] = True
        cases.append(changed)
        changed = deepcopy(self.event)
        changed['payload']['health'] = []
        cases.append(changed)
        changed = deepcopy(self.event)
        changed['payload']['roster']['save_sha256'] = 'invalid'
        cases.append(changed)
        changed = deepcopy(self.event)
        changed['owner_id'] = 'spoofed'
        cases.append(changed)
        for event in cases:
            with self.subTest(event=event.get('event_type')):
                self.assertEqual(self.post(event)[0], 400)
        for body in (b'bad JSON', b'{"schema_version":1,"schema_version":1}', b'{"value":NaN}', b'\xff'):
            self.assertEqual(self.post(body=body)[0], 400)
        self.assertEqual(self.rows(), [])

    def test_body_size_and_content_type(self):
        self.assertEqual(self.post(headers={'Content-Type': 'text/plain'})[0], 415)
        self.assertEqual(self.post(body=b'', headers={'Content-Length': str(MAX_BODY + 1)})[0], 413)
        self.assertEqual(self.post(body=b'')[0], 413)
        self.assertEqual(self.post(body=b'', headers={'Content-Length': '-1'})[0], 400)
        self.assertEqual(self.post(body=b'', headers={'Transfer-Encoding': 'chunked'})[0], 400)

    def test_storage_failure_is_not_acknowledged(self):
        with patch('bridge.receive_api.store_event', side_effect=sqlite3.OperationalError('locked')):
            self.assertEqual(self.post(), (503, {'error': 'storage_unavailable'}))
        self.assertEqual(self.rows(), [])
        self.assertEqual(self.post()[0], 201)

    def test_health_unknown_path_and_loopback_binding(self):
        self.assertEqual(self.server.server_address[0], '127.0.0.1')
        self.assertEqual(self.post(path='/health', method='GET'), (200, {'status': 'ok'}))
        self.assertEqual(self.post(path='/unknown')[0], 404)

    def test_bad_configuration_and_wrong_database_fail(self):
        for token, allowed in (('', [self.event['dynasty_id']]), (self.token, []), (self.token, ['invalid'])):
            with self.subTest(token=bool(token)), self.assertRaises(ValueError):
                create_server(self.path, token, 'owner', allowed, 0)
        wrong = self.path.parent / 'bridge.sqlite3'
        connection = sqlite3.connect(wrong)
        connection.execute('CREATE TABLE dynasties (name TEXT)')
        connection.close()
        with self.assertRaises(ValueError):
            initialize_receiver(wrong)

    def test_storage_namespaces_event_ids_by_configured_owner(self):
        event = decode_event(json.dumps(self.event).encode())
        self.assertEqual(store_event(self.path, 'owner-a', event), 'stored')
        self.assertEqual(store_event(self.path, 'owner-b', event), 'stored')
        self.assertEqual(len(self.rows()), 2)

    def test_lone_surrogate_rejected_and_unicode_name_supported(self):
        changed = deepcopy(self.event)
        changed['payload']['roster']['team']['name'] = '\ud800'
        self.assertEqual(self.post(changed)[0], 400)
        self.assertEqual(self.rows(), [])
        changed['payload']['roster']['team']['name'] = 'Montréal'
        self.assertEqual(self.post(changed)[0], 201)

    def test_missing_primary_key_rejected_at_startup(self):
        path = self.path.parent / 'invalid-receiver.sqlite3'
        connection = sqlite3.connect(path)
        try:
            connection.execute('''CREATE TABLE received_events (
                owner_id TEXT NOT NULL, event_id TEXT NOT NULL, dynasty_id TEXT NOT NULL,
                event_json TEXT NOT NULL, received_at TEXT NOT NULL)''')
            connection.execute(f'PRAGMA application_id={APPLICATION_ID}')
            connection.execute('PRAGMA user_version=1')
            connection.commit()
        finally:
            connection.close()
        with self.assertRaisesRegex(ValueError, 'structure'):
            initialize_receiver(path)

    def test_real_insert_failure_rolls_back_and_recovers(self):
        connection = sqlite3.connect(self.path)
        try:
            connection.execute('''CREATE TRIGGER reject_insert BEFORE INSERT ON received_events
                BEGIN SELECT RAISE(ABORT, 'synthetic failure'); END''')
            connection.commit()
            self.assertEqual(self.post()[0], 503)
            self.assertEqual(self.rows(), [])
            connection.execute('DROP TRIGGER reject_insert')
            connection.commit()
        finally:
            connection.close()
        self.assertEqual(self.post()[0], 201)


if __name__ == '__main__':
    unittest.main()
