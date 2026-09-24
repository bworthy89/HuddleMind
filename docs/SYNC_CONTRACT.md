# Observation sync contract — version 1

Initial Milestone 5 design; no endpoint is deployed yet.

## Implemented local outbox

```powershell
python -m bridge.queue_observation DYNASTY_ID OBSERVATION_ID
```

Use `--database PATH` for a non-default database. Version 3 is required. The
command records an event locally and prints its ID, observation, queue time,
and status; it does not transmit anything. Repeating it for the same observation
and contract version returns the original entry without rebuilding JSON or
resetting delivery state. One immediate transaction serializes competing writers.

`bridge.outbox.list_pending_events(path, dynasty_id)` reads pending entries in
queue insertion order with their exact stored JSON. Consumers must send that JSON,
not call the event builder again. Ownership is checked using the observation's
dynasty. Missing observations, incompatible databases, serialization failures,
and failed inserts produce no partial queued event.

Tested with temporary databases, concurrent writers, and a separate Python
process. The local receiver now implements authentication and acknowledgments;
the sender now handles delivery, acknowledgment processing, and bounded retries.
See [Sending observations](SENDING_OBSERVATIONS.md). Background scheduling and
hosted deployment remain future work.

The bridge sends normalized observations from SQLite. The local database remains
usable offline. Raw save files and local filesystem paths are not request fields.

## Event envelope

| Field | Meaning |
| --- | --- |
| `schema_version` | Integer `1`, the wire-contract version (not SQLite's version) |
| `event_id` | UUID assigned once when queued and persisted for every retry |
| `event_type` | `dynasty.observation.captured` |
| `dynasty_id` | HuddleMind dynasty UUID; access must be checked against the authenticated owner |
| `observed_at` | Original observation capture time in ISO 8601 UTC; not upload time |
| `payload` | Stored normalized snapshot: roster, season, schedule, depth_chart, health, recruiting |

The payload retains source hashes and snapshot-scoped record IDs. Local SQLite
observation numbers are not globally unique and are not server event identifiers.
Unknown enum values and unavailable sections remain explicit.

## Implemented local endpoint behavior

See [Receiving API](RECEIVING_API.md) for startup, credentials, dynasty access,
status codes, and limits. This is a loopback development server; hosted deployment
and production account authentication remain future work.

`POST /v1/observations` accepts the envelope and returns its `event_id` with
`status: stored` after a durable commit. Repeating the same event with the same
content returns `status: already_stored`. Reusing its ID with different content
returns a conflict and must never overwrite the original event.

The server must validate the envelope and payload, authenticate the bridge,
authorize access to the dynasty, and enforce uniqueness atomically within the
owner's scope. Identity is established by credentials, not by a caller-supplied
owner field. Capture time is distinct from server receipt time and arrival order
must not be assumed to represent game chronology.

## Implemented command-driven delivery

Persist the event ID and exact payload in a local outbox before attempting HTTP.
Retries reuse both. Mark delivery complete only after a matching server
acknowledgment. Network failures, timeouts, throttling, and transient server errors
retain pending events with bounded retry delays. Validation/conflict errors need
attention; authentication failures wait for credential recovery.

The sender processes one pending batch and stops on the first failed event.
Retries are bounded within each run; persistent scheduling remains future work.
The event model, outbox, local API, and sender/retry tests are implemented.
Authenticated hosted deployment is still pending.
Supabase remains a backend candidate; this contract does not require a provider.
