# Observation sync contract — version 1

Initial Milestone 5 design; no endpoint is deployed yet.

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

## Proposed endpoint behavior

`POST /v1/observations` accepts the envelope and returns its `event_id` with
`status: stored` after a durable commit. Repeating the same event with the same
content returns `status: already_stored`. Reusing its ID with different content
returns a conflict and must never overwrite the original event.

The server must validate the envelope and payload, authenticate the bridge,
authorize access to the dynasty, and enforce uniqueness atomically within the
owner's scope. Identity is established by credentials, not by a caller-supplied
owner field. Capture time is distinct from server receipt time and arrival order
must not be assumed to represent game chronology.

## Planned delivery behavior

Persist the event ID and exact payload in a local outbox before attempting HTTP.
Retries reuse both. Mark delivery complete only after a matching server
acknowledgment. Network failures, timeouts, throttling, and transient server errors
retain pending events with bounded retry delays. Validation/conflict errors need
attention; authentication failures wait for credential recovery.

Implementation order: event model and serialization, persistent outbox, local API
with duplicate handling, sender/retry tests, then authenticated hosted deployment.
Supabase remains a backend candidate; this contract does not require a provider.
