"""Validate the hosted adapter without contacting a VPS or using real saves."""
from copy import deepcopy
from http.client import HTTPConnection
from io import BytesIO
import json
from pathlib import Path
import tempfile
from threading import Thread
import unittest
from uuid import uuid4

from bridge.hosted_receiver import create_app
from bridge.test_receive_api import valid_event


class HostedReceiverTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.event = valid_event()
        self.token = 'synthetic-hosted-token-' + 'x' * 32
        self.path = Path(folder.name) / 'receiver.sqlite3'
        self.app = create_app(self.path, self.token, 'owner', [self.event['dynasty_id']])

    def request(self, event=None, **overrides):
        body = json.dumps(event or self.event).encode()
        environ = dict(PATH_INFO='/v1/observations', REQUEST_METHOD='POST',
                       HTTP_AUTHORIZATION='Bearer ' + self.token,
                       CONTENT_TYPE='application/json', CONTENT_LENGTH=str(len(body)))
        environ['wsgi.input'] = BytesIO(body)
        environ.update(overrides)
        received = []
        result = b''.join(self.app(environ, lambda status, headers: received.append(status)))
        return int(received[0].split()[0]), json.loads(result)

    def test_commit_duplicate_and_conflict(self):
        self.assertEqual(self.request()[0], 201)
        self.assertEqual(self.request()[1]['status'], 'already_stored')
        changed = deepcopy(self.event)
        changed['payload']['roster']['team']['name'] = 'Different'
        self.assertEqual(self.request(changed)[0], 409)

    def test_auth_routes_and_authorization(self):
        self.assertEqual(self.request(HTTP_AUTHORIZATION='')[0], 401)
        self.assertEqual(self.request(PATH_INFO='/other')[0], 404)
        self.assertEqual(self.request(REQUEST_METHOD='DELETE')[0], 405)
        self.assertEqual(self.request(PATH_INFO='/health', REQUEST_METHOD='GET')[0], 200)
        changed = deepcopy(self.event)
        changed['dynasty_id'] = str(uuid4())
        self.assertEqual(self.request(changed)[0], 403)

    def test_body_rejection(self):
        for override, code in [({'CONTENT_LENGTH': '-1'}, 400),
                               ({'CONTENT_LENGTH': '3000000'}, 413),
                               ({'CONTENT_TYPE': 'text/plain'}, 415),
                               ({'wsgi.input': BytesIO(b'bad')}, 400)]:
            self.assertEqual(self.request(**override)[0], code)

    def test_configuration_requires_identity_and_token(self):
        for token, owner, ids in [('', 'owner', [self.event['dynasty_id']]),
                                  (self.token, '', [self.event['dynasty_id']]),
                                  (self.token, 'owner', [])]:
            with self.assertRaises(ValueError):
                create_app(self.path, token, owner, ids)

    def test_waitress_real_http_delivery(self):
        try:
            from waitress import create_server
        except ImportError:
            self.skipTest('Install deploy/requirements.txt to test production HTTP')
        channels = {}
        server = create_server(self.app, host='127.0.0.1', port=0, map=channels)
        thread = Thread(target=server.run, daemon=True)
        thread.start()
        try:
            for expected in (201, 200):
                client = HTTPConnection('127.0.0.1', int(server.effective_port), timeout=5)
                try:
                    client.request('POST', '/v1/observations', json.dumps(self.event),
                                   {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + self.token})
                    response = client.getresponse()
                    self.assertEqual(response.status, expected)
                    self.assertEqual(json.loads(response.read())['event_id'], self.event['event_id'])
                finally:
                    client.close()
        finally:
            server.close()
            server.task_dispatcher.shutdown()
            for channel in list(channels.values()):
                channel.close()
            thread.join(timeout=5)
        self.assertFalse(thread.is_alive())
