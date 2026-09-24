"""WSGI receiver for Waitress behind an HTTPS reverse proxy."""
import hmac
from http import HTTPStatus
import json
import os
from pathlib import Path
import sqlite3

from bridge.receive_api import MAX_BODY
from bridge.receiver_store import initialize_receiver, store_event, EventConflict
from bridge.validate_event import decode_event, uuid_text
from bridge.bridge_health import initialize_health, validate_report, store_health, read_health


def create_app(path, token, owner_id, dynasty_ids, *, read_token=None):
    if not isinstance(token, str) or len(token) < 32 or not token.isascii() or any(c.isspace() for c in token):
        raise ValueError('Receiver token must be at least 32 non-whitespace ASCII characters')
    if not isinstance(owner_id, str) or not owner_id.strip():
        raise ValueError('Owner ID cannot be blank')
    allowed = frozenset(uuid_text(value) for value in dynasty_ids)
    if not allowed:
        raise ValueError('At least one authorized dynasty is required')
    initialize_receiver(path)
    initialize_health(path)
    if read_token is not None and (len(read_token) < 32 or not read_token.isascii()
                                  or any(c.isspace() for c in read_token) or read_token == token):
        raise ValueError('Web reader requires a separate strong credential')

    def application(environ, start_response):
        def respond(status, value):
            body = json.dumps(value).encode('utf-8')
            start_response(f'{status} {HTTPStatus(status).phrase}', [
                ('Content-Type', 'application/json'), ('Content-Length', str(len(body))),
                ('Cache-Control', 'no-store')])
            return [body]

        route, method = environ.get('PATH_INFO'), environ.get('REQUEST_METHOD')
        if route == '/v1/dashboard':
            supplied = environ.get('HTTP_AUTHORIZATION', '').encode('utf-8')
            if read_token is None or not hmac.compare_digest(supplied, ('Bearer ' + read_token).encode('ascii')):
                return respond(401, {'error': 'unauthorized'})
            if method != 'GET':
                return respond(405, {'error': 'method_not_allowed'})
            from bridge.dashboard_api import dashboard
            try:
                return respond(200, dashboard(path, owner_id, allowed))
            except (sqlite3.Error, ValueError):
                return respond(503, {'error': 'storage_unavailable'})
        if route not in ('/health', '/v1/observations', '/v1/bridge-health'):
            return respond(404, {'error': 'not_found'})
        supplied = environ.get('HTTP_AUTHORIZATION', '').encode('utf-8')
        if not hmac.compare_digest(supplied, ('Bearer ' + token).encode('ascii')):
            return respond(401, {'error': 'unauthorized'})
        if route == '/health' and method == 'GET':
            return respond(200, {'status': 'ok'})
        if route == '/v1/bridge-health' and method == 'GET':
            try:
                return respond(200, {'bridges': read_health(path, owner_id, allowed)})
            except sqlite3.Error:
                return respond(503, {'error': 'storage_unavailable'})
        if route not in ('/v1/observations', '/v1/bridge-health') or method != 'POST':
            return respond(405, {'error': 'method_not_allowed'})
        if environ.get('CONTENT_TYPE', '').split(';')[0].strip().lower() != 'application/json':
            return respond(415, {'error': 'expected_application_json'})
        length = environ.get('CONTENT_LENGTH', '')
        if not length.isascii() or not length.isdigit() or len(length) > 10:
            return respond(400, {'error': 'invalid_content_length'})
        size = int(length)
        if not 0 < size <= (4096 if route == '/v1/bridge-health' else MAX_BODY):
            return respond(413, {'error': 'body_size_limit'})
        try:
            body = environ['wsgi.input'].read(size)
            if len(body) != size:
                raise ValueError('Incomplete body')
            event = validate_report(body) if route == '/v1/bridge-health' else decode_event(body)
        except (ValueError, OSError, RecursionError):
            return respond(400, {'error': 'invalid_event'})
        if event['dynasty_id'] not in allowed:
            return respond(403, {'error': 'dynasty_not_authorized'})
        try:
            if route == '/v1/bridge-health':
                store_health(path, owner_id, event)
                return respond(200, {'status': 'received'})
            result = store_event(path, owner_id, event)
        except EventConflict:
            return respond(409, {'error': 'event_content_conflict', 'event_id': event['event_id']})
        except sqlite3.Error:
            return respond(503, {'error': 'storage_unavailable'})
        return respond(201 if result == 'stored' else 200,
                       {'event_id': event['event_id'], 'status': result})
    return application


def main():
    from waitress import serve
    # Secrets are supplied at runtime, never baked into the image.
    app = create_app(Path(os.environ.get('HUDDLEMIND_RECEIVER_DATABASE', '/data/receiver.sqlite3')),
                     os.environ.get('HUDDLEMIND_RECEIVER_TOKEN', ''),
                     os.environ.get('HUDDLEMIND_OWNER_ID', ''),
                     os.environ.get('HUDDLEMIND_DYNASTY_IDS', '').split(),
                     read_token=os.environ.get('HUDDLEMIND_READ_TOKEN') or None)
    serve(app, host='0.0.0.0', port=8080, threads=4,
          max_request_body_size=MAX_BODY, max_request_header_size=16384,
          channel_timeout=30, connection_limit=100, expose_tracebacks=False)


if __name__ == '__main__':
    main()
