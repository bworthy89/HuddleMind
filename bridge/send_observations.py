"""Send pending observations with bounded retries and verified acknowledgments."""
import argparse
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import http.client
import json
import math
import os
from pathlib import Path
import sqlite3
import time
from urllib.parse import urlsplit

from bridge.outbox import list_pending_events, mark_delivered

RETRY_STATUSES = {408, 429, 500, 502, 503, 504}
MAX_ACK_BYTES = 4096


class DeliveryError(ValueError):
    """Delivery remains pending and can safely be attempted again."""


def receiver_address(url):
    address = urlsplit(url)
    if (address.scheme not in ('http', 'https') or not address.hostname
            or address.username is not None or address.password is not None
            or address.query or address.fragment or address.path not in ('', '/')
            or any(c.isspace() for c in url)):
        raise ValueError('Receiver must be an HTTP(S) origin without credentials, path, query, or fragment')
    if address.scheme == 'http' and address.hostname not in ('127.0.0.1', '::1', 'localhost'):
        raise ValueError('Remote receivers require HTTPS')
    # Accessing port also validates malformed and out-of-range port values.
    return address.scheme, address.hostname, address.port


def post_event(address, token, body, timeout):
    scheme, host, port = address
    connection_type = http.client.HTTPSConnection if scheme == 'https' else http.client.HTTPConnection
    connection = connection_type(host, port=port, timeout=timeout)
    try:
        # Direct connections avoid proxy credential forwarding; redirects are never followed.
        connection.request('POST', '/v1/observations', body=body,
                           headers={'Authorization': 'Bearer ' + token,
                                    'Content-Type': 'application/json'})
        response = connection.getresponse()
        return (response.status, response.getheader('Content-Type', ''),
                response.getheader('Retry-After'), response.read(MAX_ACK_BYTES + 1))
    finally:
        connection.close()


def receiver_origin(address):
    scheme, host, port = address
    host = '[' + host + ']' if ':' in host else host
    suffix = '' if port is None or port == (443 if scheme == 'https' else 80) else ':' + str(port)
    return f'{scheme}://{host}{suffix}'


def retry_delay(header, attempt):
    delay = min(2 ** (attempt - 1), 30)
    if header:
        try:
            seconds = int(header) if header.isascii() and header.isdigit() else (
                parsedate_to_datetime(header) - datetime.now(timezone.utc)).total_seconds()
            delay = max(delay, seconds)
        except (ValueError, TypeError, OverflowError):
            pass
    if delay > 60:
        raise DeliveryError('Receiver requested a longer retry delay; retry later')
    return delay


def verify_ack(status, content_type, body, event_id):
    def unique_pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('Duplicate acknowledgment field')
            result[key] = value
        return result
    try:
        if len(body) > MAX_ACK_BYTES or content_type.split(';')[0].strip().lower() != 'application/json':
            raise ValueError('Invalid acknowledgment body')
        ack = json.loads(body.decode('utf-8'), object_pairs_hook=unique_pairs)
        expected = 'stored' if status == 201 else 'already_stored'
        if ack != {'event_id': event_id, 'status': expected}:
            raise ValueError('Mismatched acknowledgment')
    except (ValueError, UnicodeError, RecursionError) as error:
        raise DeliveryError('Receiver returned an invalid acknowledgment; event remains pending') from error


def send_pending(path, dynasty_id, receiver, token, *, attempts=3, timeout=10):
    """Drain this dynasty's current pending batch; stop at the first failed event."""
    address = receiver_address(receiver)
    destination = receiver_origin(address)
    if not isinstance(token, str) or len(token) < 32 or not token.isascii() or any(c.isspace() for c in token):
        raise ValueError('Sender token must be at least 32 non-whitespace ASCII characters')
    if type(attempts) is not int or not 1 <= attempts <= 5:
        raise ValueError('Attempts must be between 1 and 5')
    if not math.isfinite(timeout) or not 0 < timeout <= 60:
        raise ValueError('Timeout must be greater than zero and at most 60 seconds')
    delivered = 0
    for event in list_pending_events(path, dynasty_id, destination):
        # Send the persisted bytes unchanged on every attempt, including after restart.
        body = event.event_json.encode('utf-8')
        for attempt in range(1, attempts + 1):
            retry_after = None
            try:
                status, content_type, retry_after, response = post_event(address, token, body, timeout)
            except (OSError, http.client.HTTPException):
                failure = 'Connection failed'
            else:
                if status in (200, 201):
                    verify_ack(status, content_type, response, event.event_id)
                    mark_delivered(path, dynasty_id, event, destination)
                    delivered += 1
                    break
                failure = f'Receiver returned HTTP {status}'
                if status not in RETRY_STATUSES:
                    raise DeliveryError(f'{failure}; event {event.event_id} remains pending')
            if attempt == attempts:
                raise DeliveryError(f'{failure} after {attempts} attempts; event {event.event_id} remains pending')
            time.sleep(retry_delay(retry_after, attempt))
    return delivered


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('dynasty_id')
    parser.add_argument('--receiver', default='http://127.0.0.1:8765')
    parser.add_argument('--database', type=Path, default=Path('local_data/huddlemind.sqlite3'))
    parser.add_argument('--attempts', type=int, default=3)
    parser.add_argument('--timeout', type=float, default=10)
    args = parser.parse_args()
    try:
        count = send_pending(args.database, args.dynasty_id, args.receiver,
                             os.environ.get('HUDDLEMIND_RECEIVER_TOKEN', ''),
                             attempts=args.attempts, timeout=args.timeout)
    except (OSError, ValueError, sqlite3.Error) as error:
        parser.exit(1, f'Could not send observations: {error}\n')
    except KeyboardInterrupt:
        parser.exit(130, 'Sender stopped; unacknowledged events remain pending.\n')
    print('Delivered observations:', count)


if __name__ == '__main__':
    main()
