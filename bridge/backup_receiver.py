"""Create consistent SQLite backups and verify restoration without touching live data."""
import argparse
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import uuid


def inspect_database(path):
    # Read-only mode prevents a typo from silently creating an empty database.
    with closing(sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True)) as db:
        if db.execute('PRAGMA integrity_check').fetchall() != [('ok',)]:
            raise ValueError('Receiver database failed integrity check')
        if (db.execute('PRAGMA application_id').fetchone()[0],
                db.execute('PRAGMA user_version').fetchone()[0]) != (1213022797, 1):
            raise ValueError('Not a supported receiver database')
        digest = hashlib.sha256()
        count = 0
        for row in db.execute('SELECT owner_id, event_id, dynasty_id, event_json, received_at '
                              'FROM received_events ORDER BY owner_id, event_id'):
            digest.update(json.dumps(row, ensure_ascii=True).encode('utf-8'))
            count += 1
        return count, digest.hexdigest()


def copy_database(source, destination):
    # SQLite's backup API includes committed WAL content while the receiver runs.
    with closing(sqlite3.connect(source.resolve().as_uri() + '?mode=ro', uri=True)) as src:
        with closing(sqlite3.connect(destination)) as dst:
            src.backup(dst)


def verify_restore(backup):
    expected = inspect_database(backup)
    with tempfile.TemporaryDirectory(prefix='huddlemind-restore-') as temporary:
        restored = Path(temporary) / 'restored.sqlite3'
        copy_database(backup, restored)
        if inspect_database(restored) != expected:
            raise ValueError('Restored receiver content differs from backup')
    return expected[0]


def backup_receiver(source, directory, *, keep=14):
    if keep < 1:
        raise ValueError('Keep must be at least one backup')
    directory.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    target = directory / f'receiver-{stamp}-{uuid.uuid4().hex}.sqlite3'
    temporary = target.with_suffix('.partial')
    try:
        copy_database(source, temporary)
        temporary.chmod(0o600)
        count = verify_restore(temporary)
        temporary.rename(target)
    finally:
        temporary.unlink(missing_ok=True)
    # Prune only our timestamped backups, and only after the new restore passes.
    import re
    candidates = sorted(p for p in directory.iterdir() if p.is_file() and re.fullmatch(
        r'receiver-\d{8}T\d{12}Z-[0-9a-f]{32}\.sqlite3', p.name))
    for old in candidates[:-keep]:
        old.unlink()
    return target, count


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--keep', type=int, default=14)
    args = parser.parse_args()
    target, count = backup_receiver(args.source, args.directory, keep=args.keep)
    print(f'Backup verified: {target.name} | Restored events: {count}')


if __name__ == '__main__':
    main()
