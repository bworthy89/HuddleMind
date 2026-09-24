# Sending queued observations

## Configured hosted connection

On the owner's Windows PC, run `.\bridge\send_hosted.ps1` from the repository
root. It uses the hosted HTTPS endpoint and a Windows DPAPI-protected credential
in ignored `local_data/hosted-token.xml`. Only the same Windows account on this
PC can decrypt that credential. The helper restores the prior token environment
variable on exit.

Database version 4 adds `sync_deliveries`, keyed by event ID and canonical receiver
origin. The sender uses those receipts, so locally delivered events can reach the
hosted receiver using their original IDs and JSON. Hostname case, default ports,
and trailing slash normalize to the same origin. Changing owner or rebuilding
storage at an existing origin still requires a separate migration.

Legacy `sync_outbox.delivered_at` values remain historical first-delivery times;
the migration does not invent a destination for them. Legacy events may therefore
retry once against their former receiver, which safely acknowledges duplicates.
The no-destination `list_pending_events` call retains legacy semantics; destination
status requires passing the receiver origin.

The owner's database was backed up and upgraded without changing existing rows.
One real observation reached the hosted receiver, and subsequent sends reported
zero. Full suite: 204 passing tests.

The sender transmits pending events from the local outbox to the receiving API.
It uses their exact stored JSON and event IDs. It does not load game saves or
create new observations.

Start the [receiver](RECEIVING_API.md), then run this from the project root in a
second terminal with the virtual environment active:

```powershell
# Set this to the SAME token configured in the running receiver.
$env:HUDDLEMIND_RECEIVER_TOKEN = "YOUR_RECEIVER_TOKEN"
python -m bridge.send_observations "YOUR_DYNASTY_UUID"
```

Environment variables are terminal-local; independently generating a token in
the sender terminal will not match the running receiver. Never commit the token.
The command defaults to `http://127.0.0.1:8765` and
`local_data/huddlemind.sqlite3`. Override with `--receiver` and `--database`.
Remote destinations require HTTPS with normal certificate verification.
URLs must be origins without embedded credentials, paths, queries, or fragments.
Redirects are not followed and environment proxy settings are not used.

Successful output is `Delivered observations: N`. An empty queue reports zero
without a network request. The command drains the batch pending when it starts;
newly queued events are handled on the next run.

## Acknowledgments and retries

- HTTP 201 must return the matching event ID and `status: stored`.
- HTTP 200 must return the matching event ID and `status: already_stored`.
- Only a valid JSON acknowledgment marks the local event delivered. Its message,
  capture time, queue time, and ID remain unchanged. Repeated marks preserve the
  first delivery timestamp.
- Lost responses are safe to retry. If the receiver already committed the event,
  it returns `already_stored` on retry. If local delivery marking fails after a
  server commit, running the command again completes that same process.
- Connection errors and HTTP 408, 429, 500, 502, 503, and 504 retry up to three
  total attempts by default, with one- and two-second delays. `--attempts` allows
  1–5 attempts; `--timeout` controls the socket timeout (default 10, maximum 60
  seconds). Numeric and HTTP-date Retry-After values can extend the delay.
- A Retry-After longer than 60 seconds stops the command for a later run.
  Other HTTP errors, redirects, and invalid acknowledgments stop immediately.
- On failure the event and subsequent events remain pending; events already
  acknowledged stay delivered. Exit code is 1 on failure and 130 on Ctrl+C.

Retries are bounded within each invocation. There is no background scheduler or
persistent next-attempt timer yet. After fixing credentials, a conflict, or an
invalid event, rerun the command. Do not generate a replacement event ID merely
to bypass a conflict.

## Tests

Thirteen sender tests cover real local HTTP delivery, lost responses, immutable
retry bodies, bounded backoff, Retry-After, permanent failures, malformed/mismatched
acknowledgments, local marking failure and recovery, dynasty isolation, batch
ordering, interruption, configuration, and CLI output. Full suite: 192 tests.
Tests use synthetic snapshots and temporary databases. The user's real pending
event was not transmitted as part of this implementation.

```powershell
python -m unittest bridge.test_send_observations -v
```
