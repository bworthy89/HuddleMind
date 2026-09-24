from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from uuid import uuid4

from bridge.bridge_health import (capture_status, local_report, initialize_health,
    store_health, read_health, validate_report)
from bridge.backup_receiver import backup_receiver, inspect_database
from bridge.local_store import initialize_database, create_dynasty
from bridge.receiver_store import initialize_receiver
from bridge.sync_hosted import synchronize
from bridge import test_hosted_receiver


def report(dynasty):
    return dict(dynasty_id=dynasty, capture_running=False, last_capture_at=None,
                last_delivery_at=None, pending_count=0, capture_error=None, delivery_error=None)


class HealthTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.db = self.root / 'local.sqlite3'
        initialize_database(self.db)
        self.dynasty = create_dynasty(self.db, 'Synthetic')
        self.remote = self.root / 'receiver.sqlite3'
        initialize_receiver(self.remote)
        initialize_health(self.remote)

    def test_unknown_online_offline_and_owner_isolation(self):
        self.assertEqual(read_health(self.remote, 'a', [self.dynasty])[0]['status'], 'unknown')
        store_health(self.remote, 'a', report(self.dynasty))
        self.assertEqual(read_health(self.remote, 'a', [self.dynasty])[0]['status'], 'online')
        future = datetime.now(timezone.utc) + timedelta(minutes=16)
        self.assertEqual(read_health(self.remote, 'a', [self.dynasty], now=future)[0]['status'], 'offline')
        self.assertEqual(read_health(self.remote, 'b', [self.dynasty])[0]['status'], 'unknown')
        self.assertEqual(read_health(self.remote, 'a', [str(uuid4())])[0]['status'], 'unknown')

    def test_local_capture_success_error_stopped_and_stale(self):
        origin = 'https://example.com'
        capture_status(self.db, self.dynasty, success=True)
        first = local_report(self.db, self.dynasty, origin)
        self.assertTrue(first['capture_running'])
        self.assertIsNotNone(first['last_capture_at'])
        capture_status(self.db, self.dynasty, error='capture_failed', stopped=True)
        current = local_report(self.db, self.dynasty, origin)
        self.assertFalse(current['capture_running'])
        self.assertEqual(current['last_capture_at'], first['last_capture_at'])
        self.assertEqual(current['capture_error'], 'capture_failed')
        old = (datetime.now(timezone.utc) - timedelta(minutes=4)).isoformat()
        with patch('bridge.bridge_health.utc_now', return_value=old):
            capture_status(self.db, self.dynasty)
        self.assertFalse(local_report(self.db, self.dynasty, origin)['capture_running'])

    def test_invalid_fields_and_values(self):
        for key, value in [('pending_count', True), ('pending_count', -1), ('capture_running', 1),
                           ('last_capture_at', '2026-01-01'), ('delivery_error', 'secret path'),
                           ('dynasty_id', 'invalid'), ('extra', 1)]:
            data = report(self.dynasty)
            data[key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                validate_report(json.dumps(data).encode())
        with self.assertRaises(ValueError):
            validate_report(b'{"a":1,"a":2}')

    def test_backup_preserves_health_and_event_content(self):
        store_health(self.remote, 'owner', report(self.dynasty))
        target, _ = backup_receiver(self.remote, self.root / 'backups')
        self.assertEqual(inspect_database(target), inspect_database(self.remote))
        self.assertEqual(read_health(target, 'owner', [self.dynasty]),
                         read_health(self.remote, 'owner', [self.dynasty]))

    def test_health_sent_even_after_delivery_failure(self):
        with patch('bridge.sync_hosted.send_pending', side_effect=OSError), \
                patch('bridge.sync_hosted.health_request') as send:
            self.assertFalse(synchronize(self.db, self.dynasty, 'https://example.com', 'x' * 32))
            self.assertEqual(send.call_args.args[2]['delivery_error'], 'delivery_failed')

    def test_idle_sender_reports_without_new_save(self):
        with patch('bridge.sync_hosted.send_pending', return_value=0), \
                patch('bridge.sync_hosted.health_request') as send:
            self.assertTrue(synchronize(self.db, self.dynasty, 'https://example.com', 'x' * 32))
            self.assertEqual(send.call_args.args[2]['pending_count'], 0)


class HealthApiTests(unittest.TestCase):
    def test_health_api_auth_allowlist_and_persistence(self):
        fixture = test_hosted_receiver.HostedReceiverTests()
        fixture.setUp()
        try:
            request = lambda data=None, **kw: fixture.request(data or report(fixture.event['dynasty_id']),
                                                             PATH_INFO='/v1/bridge-health', **kw)
            self.assertEqual(request(HTTP_AUTHORIZATION='')[0], 401)
            self.assertEqual(request(report(str(uuid4())))[0], 403)
            self.assertEqual(request()[0], 200)
            status, data = request(REQUEST_METHOD='GET')
            self.assertEqual(status, 200)
            self.assertEqual(data['bridges'][0]['status'], 'online')
            self.assertEqual(request(CONTENT_LENGTH='4097')[0], 413)
            self.assertEqual(request(REQUEST_METHOD='DELETE')[0], 405)
        finally:
            fixture.doCleanups()
