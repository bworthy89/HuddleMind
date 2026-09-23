# Local Memory checkpoint

Milestone 4's initial storage scope is implemented: dynasty identities, complete
observations, capture/history commands, schema upgrades, and recommendation history.
The game save is never modified. Local databases and their backups are ignored by Git.

## Database versions

`initialize_database()` handles fresh databases and compatible version-0/1
databases. Version 2 adds recommendations and recommendation events. Initialization
validates the original columns, relationships, unique constraint, and foreign-key
data before committing. A single immediate transaction covers DDL, validation,
and the version assignment; failures roll back. Newer versions are rejected.

```powershell
python -m bridge.recommendations init
```

Use `--database "PATH"` after any subcommand to select another database. `init`
can create a new database; other recommendation commands require an existing
version-2 database. Back up valuable databases before an upgrade. The owner's
first upgrade was backed up locally, and every prior dynasty/observation row was
verified unchanged, with clean SQLite integrity and foreign-key checks.

## Recommendation history

Every recommendation belongs to one stored observation. Its dynasty is derived
from that observation, preventing an independent dynasty field from drifting out
of sync. Store advice, rationale, UTC creation time, and source (for example,
`manual` or a versioned engine identifier). This feature records supplied advice;
it does not implement a recommendation engine or claim the advice is effective.

```powershell
python -m bridge.recommendations add DYNASTY_ID OBSERVATION_ID --advice "Suggested action" --rationale "Reason for the suggestion" --source manual
python -m bridge.recommendations list DYNASTY_ID
python -m bridge.recommendations show DYNASTY_ID RECOMMENDATION_ID
python -m bridge.recommendations choice DYNASTY_ID RECOMMENDATION_ID --detail "What I chose and why"
python -m bridge.recommendations outcome DYNASTY_ID RECOMMENDATION_ID --detail "What happened afterward"
```

`add` prints the new recommendation ID. `list` shows newest insertions first;
`show` returns the original recommendation and its events as JSON. The latter
reads both parts in one SQLite read transaction. Read operations use enforced
read-only connections. Unknown dynasties and mismatched observation/recommendation
IDs produce errors or no matching result, never another dynasty's data.

Choices and reported outcomes are append-only through these APIs. Recording a
correction adds another event instead of rewriting the previous entry. Multiple
choices/outcomes are allowed; a missing choice is not treated as acceptance and
an absent outcome is not treated as failure. Repeated `add`, `choice`, or `outcome`
calls intentionally create separate entries; they are not deduplicated like save
observations. Automated callers must avoid blind retries until an idempotency key
is added. Outcome text is reported evidence, not automatic causal evaluation.

## Validation and boundaries

The full suite has 146 passing synthetic tests. Migration tests cover fresh and
legacy databases, version-1 upgrades, repeat initialization, incompatible columns,
missing constraints, orphan rows, future versions, and transactional rollback.
Recommendation tests cover lifecycle, Unicode, dynasty isolation, missing links,
blank input, version rejection, separate-process persistence, rollback/recovery,
read-only retrieval, and CLI behavior. No synthetic recommendations were inserted
into the owner's database.

Observation JSON retains roster, schedule, health, depth, and recruiting from each
capture. Player record IDs are snapshot-scoped; cross-save identity matching,
automatic observation comparisons, retention policy, and automatic watcher capture
are not implemented. Recommendation scoring and automatic outcome tracking belong
to later intelligence milestones. No cloud connection is part of this checkpoint.
