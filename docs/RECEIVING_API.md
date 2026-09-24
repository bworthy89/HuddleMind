# Local receiving API

Milestone 5 now has a runnable, authenticated development receiver. It binds only
to `127.0.0.1` and uses Python's standard-library HTTP server. Hosted deployment,
TLS, account registration, and production server infrastructure are still pending.

From the repository root, with the virtual environment active:

```powershell
$env:HUDDLEMIND_RECEIVER_TOKEN = python -c "import secrets; print(secrets.token_urlsafe(32))"
python -m bridge.receive_api --owner-id "local-user" --dynasty-id "YOUR_DYNASTY_UUID"
```

Keep the token available for the future sender. Generating a new token replaces
the credential accepted by the next receiver process. Stop with Ctrl+C.
Use `--port` to change port 8765, `--database` to change
`local_data/receiver.sqlite3`, and repeat `--dynasty-id` to authorize other dynasties.
The receiver database is separate from the bridge's local history database.

Requests require `Authorization: Bearer TOKEN`. The configured owner identity and
dynasty allowlist establish access; callers cannot supply their own owner field.
`GET /health` returns `{"status":"ok"}` after authentication.

## Observation endpoint

`POST /v1/observations` accepts the version-1 envelope in
[the sync contract](SYNC_CONTRACT.md), with `Content-Type: application/json` and
an explicit Content-Length. Bodies must be nonempty and no larger than 2 MiB.
Chunked requests are not supported. Socket operations have a five-second timeout.

The receiver validates the envelope, nested snapshot field types, UTC timestamp,
source hashes, roster identities, health membership, and depth references.
Duplicate JSON keys, non-finite numbers, extra fields, and unsupported contract
versions are rejected. Unknown game enum values remain supported. Version 1 uses
the current DynastyDetails field shape; future model changes must explicitly
review wire compatibility before being released.

| HTTP status | Response / meaning |
| --- | --- |
| 201 | `event_id` and `status: stored`, after transaction commit |
| 200 | `event_id` and `status: already_stored`, identical retry |
| 400 | Invalid body, event, or Content-Length |
| 401 | Missing or incorrect bearer token |
| 403 | Dynasty is outside the configured allowlist |
| 404 | Unknown endpoint |
| 409 | Event ID already exists with different content |
| 413 | Body size outside allowed bounds |
| 415 | Content-Type is not application/json |
| 503 | Storage failed; no success acknowledgment |

One SQLite transaction serializes duplicate checks and insertion. Event IDs are
unique within the configured owner's scope. Object-key order and JSON whitespace
do not affect duplicate detection; changed content never overwrites the original.
Receipt time is stored separately from capture time and survives retries.

The receiver does not update the bridge outbox. The next implementation is the
sender: transmit exact queued JSON, validate the matching acknowledgment, then
mark that event delivered. Until then, queued observations remain pending.

## Validation

Eleven receiver tests use synthetic snapshots, temporary databases, and actual
loopback HTTP connections. They cover authentication/authorization, validation,
concurrent delivery, duplicate persistence across restart, conflicts, storage
failure, configuration guards, and owner isolation. Full bridge suite: 179 tests.

```powershell
python -m unittest bridge.test_receive_api -v
python -m unittest discover -s bridge -p "test_*.py"
```
