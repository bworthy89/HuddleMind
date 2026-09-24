# Sending queued observations

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
