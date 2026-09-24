"""Loopback-only development receiver. Not a public production HTTP server."""
import argparse
import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import sqlite3

from bridge.receiver_store import initialize_receiver, store_event, EventConflict
from bridge.validate_event import decode_event, uuid_text

MAX_BODY = 2 * 1024 * 1024


def create_server(path, token, owner_id, dynasty_ids, port=8765):
    if not isinstance(token, str) or len(token) < 32 or not token.isascii() or any(c.isspace() for c in token):
        raise ValueError('Receiver token must be at least 32 non-whitespace ASCII characters')
    if not owner_id.strip():
        raise ValueError('Owner ID cannot be blank')
    allowed = frozenset(uuid_text(value) for value in dynasty_ids)
    if not allowed:
        raise ValueError('At least one authorized dynasty is required')
    initialize_receiver(path)

    class Handler(BaseHTTPRequestHandler):
        def setup(self):
            super().setup()
            self.connection.settimeout(5)

        def log_message(self, *args):
            pass  # Do not log credentials or save-derived request content.

        def respond(self, status, value):
            data = json.dumps(value).encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Connection', 'close')
            self.end_headers()
            self.close_connection = True
            try:
                self.wfile.write(data)
            except OSError:
                pass  # A lost response is recovered by an idempotent retry.

        def authorized(self):
            values = self.headers.get_all('Authorization', [])
            supplied = values[0].encode('utf-8') if len(values) == 1 else b''
            if not hmac.compare_digest(supplied, ('Bearer ' + token).encode('ascii')):
                self.respond(401, {'error': 'unauthorized'})
                return False
            return True

        def do_GET(self):
            if self.path != '/health':
                return self.respond(404, {'error': 'not_found'})
            if self.authorized():
                self.respond(200, {'status': 'ok'})

        def do_POST(self):
            if self.path != '/v1/observations':
                return self.respond(404, {'error': 'not_found'})
            if not self.authorized():
                return
            if self.headers.get('Content-Type', '').split(';')[0].strip().lower() != 'application/json':
                return self.respond(415, {'error': 'expected_application_json'})
            sizes = self.headers.get_all('Content-Length', [])
            if self.headers.get_all('Transfer-Encoding') or len(sizes) != 1 or len(sizes[0]) > 10 or not sizes[0].isascii() or not sizes[0].isdigit():
                return self.respond(400, {'error': 'invalid_content_length'})
            size = int(sizes[0])
            if not 0 < size <= MAX_BODY:
                return self.respond(413, {'error': 'body_size_limit'})
            try:
                body = self.rfile.read(size)
                if len(body) != size:
                    raise ValueError('Incomplete body')
                event = decode_event(body)
            except (ValueError, OSError, RecursionError):
                return self.respond(400, {'error': 'invalid_event'})
            if event['dynasty_id'] not in allowed:
                return self.respond(403, {'error': 'dynasty_not_authorized'})
            try:
                result = store_event(path, owner_id, event)
            except EventConflict:
                return self.respond(409, {'error': 'event_content_conflict', 'event_id': event['event_id']})
            except sqlite3.Error:
                return self.respond(503, {'error': 'storage_unavailable'})
            self.respond(201 if result == 'stored' else 200,
                         {'event_id': event['event_id'], 'status': result})

    return ThreadingHTTPServer(('127.0.0.1', port), Handler)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', type=Path, default=Path('local_data/receiver.sqlite3'))
    parser.add_argument('--owner-id', required=True, help='Local configured identity for this credential.')
    parser.add_argument('--dynasty-id', action='append', required=True, help='Authorized dynasty UUID; repeat as needed.')
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    try:
        if not 1 <= args.port <= 65535:
            raise ValueError('Port must be between 1 and 65535')
        server = create_server(args.database, os.environ.get('HUDDLEMIND_RECEIVER_TOKEN', ''),
                               args.owner_id, args.dynasty_id, args.port)
    except (OSError, ValueError, sqlite3.Error) as error:
        parser.exit(1, f'Could not start receiver: {error}\n')
    print(f'Receiver listening on http://127.0.0.1:{args.port}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('Stopping receiver...')
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
