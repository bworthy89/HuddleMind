"""Watch one save, validate stable bytes, and atomically capture and queue it."""
import argparse
import sqlite3
import time
from pathlib import Path

from bridge.dynasty_reader import FrozenSource
from bridge.load_dynasty import load_dynasty
from bridge.local_store import DATABASE_VERSION, connect_database, get_dynasty, save_observation
from bridge.bridge_health import capture_status


def signature(path):
    stat = path.stat()
    return stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns


def capture(save, schema, database, dynasty_id, expected):
    # Freeze the inputs so every section and source hash uses identical bytes.
    if signature(save) != expected:
        raise ValueError('Save changed before reading')
    raw = save.read_bytes()
    if not raw or signature(save) != expected:
        raise ValueError('Save is empty or changed while reading')
    details = load_dynasty(FrozenSource(raw), FrozenSource(schema.read_bytes()))
    # Reject a write/replacement that happened during parsing, including same-size writes.
    if signature(save) != expected or save.read_bytes() != raw:
        raise ValueError('Save changed during validation')
    return save_observation(database, dynasty_id, details, queue=True)


class CaptureWatcher:
    def __init__(self, save, callback, *, quiet=3.0, attempts=5, report=print):
        self.save, self.callback, self.report = save, callback, report
        self.quiet, self.attempts = quiet, attempts
        self.current = None
        self.due = 0.0
        self.failures = 0
        self.finished = False
        self.missing = False

    def poll(self, now):
        try:
            current = signature(self.save)
        except OSError:
            if not self.missing:
                self.report('Waiting: selected save is missing or inaccessible.')
            self.missing = True
            self.current = None
            return
        self.missing = False
        if current != self.current:
            self.current = current
            self.due = now + self.quiet
            self.failures, self.finished = 0, False
            self.report('Change detected; waiting for save to settle.')
        if self.finished or now < self.due:
            return
        try:
            observation = self.callback(current)
        except (OSError, ValueError, sqlite3.Error, EOFError) as error:
            self.failures += 1
            if self.failures >= self.attempts:
                self.finished = True
                self.report(f'Capture needs attention: {error}. Waiting for a file change or restart.')
            else:
                self.due = now + min(30, 2 ** self.failures)
                self.report(f'Capture retry {self.failures}/{self.attempts}: {error}')
        else:
            self.finished = True
            self.report(f'Captured and queued observation: {observation}. Background sender will deliver it.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('save', type=Path)
    parser.add_argument('schema', type=Path)
    parser.add_argument('dynasty_id')
    parser.add_argument('--database', type=Path, default=Path('local_data/huddlemind.sqlite3'))
    args = parser.parse_args()
    try:
        if not args.database.is_file() or not args.schema.is_file() or not args.save.parent.is_dir():
            raise ValueError('Database, schema, and save parent directory must exist')
        if get_dynasty(args.database, args.dynasty_id, read_only=True) is None:
            raise ValueError('Dynasty not found')
        connection = connect_database(args.database, read_only=True)
        try:
            if connection.execute('PRAGMA user_version').fetchone()[0] != DATABASE_VERSION:
                raise ValueError('Initialize the database to the supported version first')
        finally:
            connection.close()
        watcher = CaptureWatcher(args.save, lambda expected: capture(
            args.save, args.schema, args.database, args.dynasty_id, expected))
        print('Watching selected save:', args.save, flush=True)
        print('Initial capture checks the current save too. Press Ctrl+C to stop.', flush=True)
        # Polling survives missed filesystem notifications and atomic file replacement.
        heartbeat = 0
        try:
            while True:
                was_finished = watcher.finished
                watcher.poll(time.monotonic())
                captured = not was_finished and watcher.finished and watcher.failures == 0
                if captured or time.monotonic() >= heartbeat:
                    capture_status(args.database, args.dynasty_id, success=captured,
                                   error='capture_failed' if watcher.failures or watcher.missing else None)
                    heartbeat = time.monotonic() + 30
                time.sleep(1)
        finally:
            capture_status(args.database, args.dynasty_id, stopped=True,
                           error='capture_failed' if watcher.failures or watcher.missing else None)
    except KeyboardInterrupt:
        print('Stopped capture watcher. Queued observations remain stored.')
    except (OSError, ValueError, sqlite3.Error) as error:
        parser.exit(1, f'Could not watch dynasty: {error}\n')


if __name__ == '__main__':
    main()
