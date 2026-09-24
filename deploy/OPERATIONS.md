# Receiver backups and background delivery

The receiver remains at `https://huddlemind-api.worthymedia.tech`.

## Receiver backups

The selected VPS runs `huddlemind-backup.timer` daily at **06:00 UTC**, with
up to five minutes of jitter and catch-up after downtime. It keeps the latest
**14 successful backups** under `/var/backups/huddlemind` (root-only access).
Extra manual runs count toward retention.

The service uses `/opt/huddlemind-ops/backup_receiver.py`, a deployed copy of
`bridge/backup_receiver.py`. SQLite's backup API captures a consistent database,
including committed WAL data. Each run checks database integrity and identity,
restores into a separate temporary database, and compares every stored row via
a content digest before publishing the backup and pruning older backups.
It never replaces the live database.

```sh
systemctl list-timers huddlemind-backup.timer
journalctl -u huddlemind-backup.service -n 20 --no-pager
systemctl start huddlemind-backup.service
```

Deployment definitions are in this directory. The service's source path is the
verified mountpoint of the `huddlemind_receiver-data` Docker volume; check it
with `docker volume inspect` before installing on a different host. Install the
Python utility in `/opt/huddlemind-ops` and the two unit files in
`/etc/systemd/system`, then reload systemd and enable the timer. Update the
deployed utility explicitly when changing backup code; a receiver image update
does not update that separate copy.

On initial activation, the backup and a downloaded private copy both restored
two events (one synthetic verification event and one real observation). The
download lives in ignored `local_data/receiver-offsite-20260924.sqlite3`.
**Ongoing off-server replication is not configured.** Daily VPS backups alone
do not protect against loss of the entire server.

To rehearse restoration again without altering production:

```powershell
python -c "from pathlib import Path; from bridge.backup_receiver import verify_restore; print(verify_restore(Path('local_data/receiver-offsite-20260924.sqlite3')))"
```

A production recovery would also require the receiver configuration/credential,
stopping writes, restoring correct volume ownership, and verifying the receiver
before reopening traffic. This checkpoint tests isolated database restoration,
not a full VPS disaster recovery or replacement of the live database.

## Windows background delivery

`deploy/install-sender-task.ps1` registers **HuddleMind Hosted Delivery** for the
current Windows user and starts it. It runs every five minutes while that user
is logged in and the PC is awake. No password or token is stored in task arguments.
The existing DPAPI credential remains in ignored `local_data/hosted-token.xml`.

The task runs hidden, ignores overlapping launches, and has a four-minute run
limit. The sender retains its bounded retries within each run; later runs retry
remaining events. Already acknowledged events are skipped by receiver origin.
Authentication or malformed-event failures also remain pending and require
correction; subsequent scheduled attempts do not repair them automatically.
Only already captured/queued observations are sent; this does not watch saves
or capture new observations.

The latest attempt replaces `local_data/hosted-delivery-status.json`. No payloads
or credentials are logged. Task Scheduler's last result is zero on success and
nonzero on failure. There is no failure notification service yet.

```powershell
Get-ScheduledTaskInfo -TaskName 'HuddleMind Hosted Delivery'
Get-Content local_data/hosted-delivery-status.json
Start-ScheduledTask -TaskName 'HuddleMind Hosted Delivery'
Disable-ScheduledTask -TaskName 'HuddleMind Hosted Delivery'
Enable-ScheduledTask -TaskName 'HuddleMind Hosted Delivery'
```

Re-run the installer after moving the repository. Run it as the same user who
saved the credential. Test coverage includes WAL-backed backups, restore
contents, duplicate receipts, retention, invalid sources, and wrapper success
and failure reporting.
