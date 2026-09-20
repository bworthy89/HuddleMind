# Read-only roster reader handoff

Update 2026-09-20: the initial implementation sequence below has been carried out through the roster command, JSON export, and position summaries. The owner confirmed selected roster values in-game. See `ROSTER_CHECKPOINT.md` for current status; broader reader/build/lifecycle limitations below still apply.

## Implementation target

The first application feature should load a stable dynasty-save snapshot and show the controlled team's roster: player name, position, and overall rating. Keep all game-file access read-only. The current discovery modules are research code to guide an adapter, not a general-purpose save parser.

## Data contract

- Snapshot: save hash, schema hash, supported format/version, validation status.
- Team: source table/row, TeamIndex, display name, roster reference.
- Coach: source table/row, name, TeamIndex, user-controlled flag.
- Player: source table/row, name, position code and label, overall rating, TeamIndex.
- Selection: resolved, no controlled coach, multiple controlled coaches, missing team, or ambiguous team.

Treat table/row identity as snapshot-local until stability across saves is established. Follow roster references; never assume team rows equal roster rows. Occupied Player records and roster members are different sets.

## Validated reader behavior

`discover_rosters.table_directory` traverses the header-declared table count from the asset-table boundary. Each table must have supported markers, matching identities/counts, consistent section lengths, a unique ID, and an in-bounds end. The supported trailer is exactly eight zero bytes. It never searches payloads for table markers.

The reader follows the free list for team, roster-array, player, and coach records used in discovery. Cycles, out-of-range links, missing references, wrong target types, and unsupported layouts raise errors. Null roster references remain explicit. A resolved roster can be empty.

Packed fields are derived from schema descriptors with full-word coverage checks. Position labels use enum values rather than member indices. TeamIndex joins are cross-checked against roster membership; mismatch details stay in the local report and should block an application-ready snapshot until resolved.

Controlled-team selection is explicit. The application must not silently choose the first of several coaches or teams. A future UI can offer selection for multiple coaches, retaining their source identities.

## Validation and limits

Eleven synthetic tests cover packed ordering, invalid rows/pointers, cyclic and invalid free lists, table boundary/trailer corruption, and all controlled-team selection outcomes. The stricter reader was also run against the available local save: decoded player values were unchanged, the controlled-team selection resolved, and roster/team joins had no mismatches. No save-derived names or report content are included here.

Still required: owner comparison with the in-game roster display. General schema inheritance, other builds, alternate table layouts/trailers, save lifecycle changes, and concurrent-save handling beyond the existing snapshot-hash check are not established. Unsupported structures should fail with a useful message rather than trigger speculative parsing. The week-advance test remains deferred.

## Suggested implementation sequence

1. Owner implements small typed snapshot/team/player models with comments and focused examples.
2. Extract the proven read-only operations into a reusable adapter with structured errors and explicit schema/version selection.
3. Expose one load operation returning a validated snapshot or a clear selection/error outcome.
4. Build a simple roster display; wire watcher notifications only after stable-file/readiness handling is defined.

The existing instructional `inspect_save.py` remains separate from the application adapter. Downloaded schemas, third-party source, and save-derived reports stay outside tracked application assets.
