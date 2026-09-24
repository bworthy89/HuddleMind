"""Synthetic delivery tests, including a real receiver and lost acknowledgments."""
from contextlib import closing, redirect_stderr, redirect_stdout
from dataclasses import replace
from io import StringIO
import json
from pathlib import Path
import sqlite3
import tempfile
from threading import Thread
import unittest
from unittest.mock import patch

from bridge.local_store import initialize_database, create_dynasty, save_observation
from bridge.outbox import queue_observation, list_pending_events, mark_delivered
from bridge.receive_api import create_server
from bridge.send_observations import send_pending, post_event, DeliveryError, main
from bridge.test_dynasty_details import sample


class SenderTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.path = Path(folder.name) / 'history.sqlite3'
        self.receiver_path = Path(folder.name) / 'receiver.sqlite3'
        initialize_database(self.path)
        self.dynasty = create_dynasty(self.path, 'Synthetic dynasty')
        details = sample()
        details = replace(details, roster=replace(details.roster, save_sha256='a' * 64, schema_sha256='b' * 64))
        self.observation = save_observation(self.path, self.dynasty, details)
        self.event = queue_observation(self.path, self.dynasty, self.observation)
        self.token = 'synthetic-sender-token-' + 'x' * 32
        self.server = create_server(self.receiver_path, self.token, 'owner', [self.dynasty], 0)
        self.thread = Thread(target=self.server.serve_forever, kwargs={'poll_interval': 0.01}, daemon=True)
        self.thread.start()
        self.url = f'http://127.0.0.1:{self.server.server_port}'

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)

    def send(self, **kwargs):
        return send_pending(self.path, self.dynasty, self.url, self.token, **kwargs)

    def ack(self, status=201, event_id=None, label='stored'):
        return status, 'application/json', None, json.dumps({
            'event_id': event_id or self.event.event_id, 'status': label}).encode()

    def test_real_receiver_delivery_and_repeat(self):
        self.assertEqual(self.send(), 1)
        saved = queue_observation(self.path, self.dynasty, self.observation)
        self.assertIsNotNone(saved.delivered_at)
        self.assertEqual(replace(saved, delivered_at=None), self.event)
        self.assertEqual(list_pending_events(self.path, self.dynasty), ())
        with patch('bridge.send_observations.post_event') as request:
            self.assertEqual(self.send(), 0)
            request.assert_not_called()
        mark_delivered(self.path, self.dynasty, self.event)
        self.assertEqual(queue_observation(self.path, self.dynasty, self.observation), saved)

    def test_lost_response_retries_exact_body_and_commits_once(self):
        sent = []
        def lose_first(*args):
            sent.append(args[2])
            result = post_event(*args)
            if len(sent) == 1:
                raise TimeoutError('Synthetic lost response after server commit')
            return result
        with patch('bridge.send_observations.post_event', side_effect=lose_first), patch('bridge.send_observations.time.sleep') as sleep:
            self.assertEqual(self.send(), 1)
            sleep.assert_called_once_with(1)
        self.assertEqual(sent, [self.event.event_json.encode()] * 2)
        with closing(sqlite3.connect(self.receiver_path)) as connection:
            self.assertEqual(connection.execute('SELECT count(*) FROM received_events').fetchone()[0], 1)

    def test_transient_failures_have_bounded_backoff(self):
        responses = [OSError('offline'), (503, '', None, b''), self.ack()]
        with patch('bridge.send_observations.post_event', side_effect=responses) as request, patch('bridge.send_observations.time.sleep') as sleep:
            self.assertEqual(self.send(), 1)
        self.assertEqual(request.call_count, 3)
        self.assertEqual([call.args[0] for call in sleep.call_args_list], [1, 2])

    def test_exhausted_retries_leave_original_event_pending(self):
        with patch('bridge.send_observations.post_event', side_effect=TimeoutError), patch('bridge.send_observations.time.sleep'), self.assertRaises(DeliveryError):
            self.send(attempts=2)
        self.assertEqual(list_pending_events(self.path, self.dynasty), (self.event,))

    def test_permanent_errors_and_redirects_do_not_retry(self):
        for status in (301, 302, 400, 401, 403, 404, 409, 413, 415):
            with self.subTest(status=status), patch('bridge.send_observations.post_event', return_value=(status, '', None, b'')) as request, self.assertRaises(DeliveryError):
                self.send()
            self.assertEqual(request.call_count, 1)
        self.assertEqual(list_pending_events(self.path, self.dynasty), (self.event,))

    def test_invalid_acknowledgments_never_mark_delivery(self):
        cases = [self.ack(event_id='wrong'), self.ack(label='unexpected'), self.ack(status=200),
                 (201, 'text/plain', None, self.ack()[3]), (201, 'application/json', None, b'bad'),
                 (201, 'application/json', None, b'x' * 4097),
                 (201, 'application/json', None, b'{"status":"stored","status":"stored"}')]
        for response in cases:
            with self.subTest(response=response[:2]), patch('bridge.send_observations.post_event', return_value=response), self.assertRaises(DeliveryError):
                self.send()
        self.assertEqual(list_pending_events(self.path, self.dynasty), (self.event,))

    def test_retry_after_and_long_delay_deferral(self):
        with patch('bridge.send_observations.post_event', side_effect=[(429, '', '5', b''), self.ack()]), patch('bridge.send_observations.time.sleep') as sleep:
            self.assertEqual(self.send(), 1)
            sleep.assert_called_once_with(5)
        with patch('bridge.send_observations.list_pending_events', return_value=(self.event,)), patch('bridge.send_observations.post_event', return_value=(429, '', '120', b'')), patch('bridge.send_observations.time.sleep') as sleep, self.assertRaises(DeliveryError):
            self.send()
        sleep.assert_not_called()

    def test_local_mark_failure_recovers_on_next_run(self):
        with patch('bridge.send_observations.mark_delivered', side_effect=sqlite3.OperationalError('locked')), self.assertRaises(sqlite3.Error):
            self.send()
        self.assertEqual(list_pending_events(self.path, self.dynasty), (self.event,))
        self.assertEqual(self.send(), 1)  # Receiver returns already_stored.

    def test_mark_checks_dynasty_and_exact_content(self):
        other = create_dynasty(self.path, 'Other')
        for dynasty, event in ((other, self.event), (self.dynasty, replace(self.event, event_json='changed'))):
            with self.assertRaises(ValueError):
                mark_delivered(self.path, dynasty, event)
        self.assertEqual(list_pending_events(self.path, self.dynasty), (self.event,))

    def test_failed_event_leaves_later_events_pending(self):
        details = sample()
        details = replace(details, roster=replace(details.roster, save_sha256='c' * 64, schema_sha256='b' * 64))
        second_id = save_observation(self.path, self.dynasty, details)
        second = queue_observation(self.path, self.dynasty, second_id)
        with patch('bridge.send_observations.post_event', return_value=(409, '', None, b'')) as request, self.assertRaises(DeliveryError):
            self.send()
        self.assertEqual(request.call_count, 1)
        self.assertEqual(list_pending_events(self.path, self.dynasty), (self.event, second))
        self.assertEqual(self.send(), 2)

    def test_interrupt_preserves_pending_event(self):
        with patch('bridge.send_observations.post_event', side_effect=KeyboardInterrupt), self.assertRaises(KeyboardInterrupt):
            self.send()
        self.assertEqual(list_pending_events(self.path, self.dynasty), (self.event,))

    def test_configuration_rejected_before_network(self):
        with patch('bridge.send_observations.post_event') as request:
            for url in ('http://example.com', 'https://user:password@example.com', 'http://127.0.0.1/path', 'http://127.0.0.1?token=x', 'ftp://example.com', 'http://127.0.0.1:99999'):
                with self.subTest(url=url), self.assertRaises(ValueError):
                    send_pending(self.path, self.dynasty, url, self.token)
            for settings in ({'attempts': 0}, {'attempts': 6}, {'timeout': 0}, {'timeout': float('nan')}):
                with self.assertRaises(ValueError):
                    self.send(**settings)
            with self.assertRaises(ValueError):
                send_pending(self.path, self.dynasty, self.url, '')
            request.assert_not_called()

    def test_cli_success_and_clean_error(self):
        arguments = ['sender', self.dynasty, '--database', str(self.path), '--receiver', self.url]
        output = StringIO()
        with patch('sys.argv', arguments), patch.dict('os.environ', {'HUDDLEMIND_RECEIVER_TOKEN': self.token}), redirect_stdout(output):
            main()
        self.assertIn('Delivered observations: 1', output.getvalue())
        error = StringIO()
        with patch('sys.argv', arguments), patch.dict('os.environ', {'HUDDLEMIND_RECEIVER_TOKEN': ''}), redirect_stderr(error), self.assertRaises(SystemExit) as stopped:
            main()
        self.assertEqual(stopped.exception.code, 1)
        self.assertIn('Could not send observations:', error.getvalue())
        self.assertNotIn(self.token, error.getvalue())


if __name__ == '__main__':
    unittest.main()
