"""Deliver queued events, then report bridge health even when delivery failed."""
import argparse
import http.client
import json
import os
from pathlib import Path
import sqlite3

from bridge.bridge_health import local_report
from bridge.send_observations import receiver_address, receiver_origin, send_pending


def health_request(receiver, token, report=None):
    if len(token) < 32 or not token.isascii() or any(c.isspace() for c in token):
        raise ValueError('Invalid sender token')
    scheme, host, port = receiver_address(receiver)
    factory = http.client.HTTPSConnection if scheme == 'https' else http.client.HTTPConnection
    connection = factory(host, port=port, timeout=10)
    try:
        connection.request('POST' if report is not None else 'GET', '/v1/bridge-health',
                           body=json.dumps(report) if report is not None else None,
                           headers={'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'})
        response = connection.getresponse()
        body = response.read(65537)
        if response.status != 200 or len(body) > 65536:
            raise ValueError('Health request failed')
        result = json.loads(body)
        if report is not None and result != {'status': 'received'}:
            raise ValueError('Invalid health acknowledgment')
        return result
    finally:
        connection.close()


def synchronize(database, dynasty, receiver, token):
    failed = False
    try:
        count = send_pending(database, dynasty, receiver, token)
        print('Delivered observations:', count)
    except (OSError, ValueError, sqlite3.Error, http.client.HTTPException):
        failed = True
        print('Delivery failed; unacknowledged events remain queued.')
    report = local_report(database, dynasty, receiver_origin(receiver_address(receiver)),
                          'delivery_failed' if failed else None)
    health_request(receiver, token, report)
    print('Bridge health reported.')
    return not failed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('dynasty_id')
    parser.add_argument('--receiver', required=True)
    parser.add_argument('--database', type=Path, default=Path('local_data/huddlemind.sqlite3'))
    parser.add_argument('--health-only', action='store_true', help='Read hosted health without sending observations.')
    args = parser.parse_args()
    try:
        token = os.environ.get('HUDDLEMIND_RECEIVER_TOKEN', '')
        if args.health_only:
            print(json.dumps(health_request(args.receiver, token), indent=2))
        elif not synchronize(args.database, args.dynasty_id, args.receiver, token):
            parser.exit(1)
    except (OSError, ValueError, sqlite3.Error, http.client.HTTPException):
        parser.exit(1, 'Could not update/read bridge health. Check connectivity, credentials, and local database.\n')


if __name__ == '__main__':
    main()
