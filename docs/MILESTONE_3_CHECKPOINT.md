# Milestone 3 implementation checkpoint — 2026-09-22

Implementation is complete for the inspected save/schema pair. Final depth-chart
and injury UI acceptance checks are deferred by the owner. The milestone is
**implemented, awaiting final manual acceptance**.

## Delivered

- Immutable coach/team/player snapshot, roster filtering, summaries and export.
- Manager-linked schedule, completed results, controlled-team orientation and summaries.
- Season context and earliest scheduled pending fixtures in the current season.
  Same-week candidates are retained together; missing weeks are not called byes.
- Team-linked depth chart with position and source slot order. Null slots stay
  explicit. Players must belong to the selected roster; duplicates within one
  position are rejected. Players can serve more than one position.
- Health records for every roster player: raw enum values and schema labels,
  injury durations, and reserve flag. Unknown values remain unknown.
- Team-linked recruiting board, hours, linked recruit/player identities, names,
  position, ranks, stage, scholarship status, and current hours. Schema-declared
  derived target types are supported. Duplicate recruits are rejected.
- One combined loader captures each source once, reusing its bytes for every section.
- Combined dynasty CLI and complete versioned JSON export with exclusive creation.

## Run

From the repository root with the virtual environment active:

```powershell
python -m bridge.show_dynasty "PATH_TO_SAVE" "PATH_TO_SCHEMA.gz"
python -m bridge.show_dynasty "PATH_TO_SAVE" "PATH_TO_SCHEMA.gz" --section depth
python -m bridge.show_dynasty "PATH_TO_SAVE" "PATH_TO_SCHEMA.gz" --section health
python -m bridge.show_dynasty "PATH_TO_SAVE" "PATH_TO_SCHEMA.gz" --section recruiting
python -m bridge.show_dynasty "PATH_TO_SAVE" "PATH_TO_SCHEMA.gz" --section all --export "local_data/dynasty-full.json"
python -m unittest discover -s bridge -p "test_*.py"
```

The export parent must exist. Existing files are never overwritten. Exports
include all sections regardless of display selection, source hashes through the
roster snapshot, and `format_version: 1`. Saves, schemas, and full exports stay local.

## Validation

The full command and temporary export passed against the inspected save. All six
sections were present, provenance matched the captured save, and the original
save hash was unchanged. The owner previously confirmed roster, schedule/results,
and season/week samples, and now confirms recruiting-board count and total hours.

All **92 synthetic tests pass**. Coverage includes compressed bounds, invalid schemas, reference types and
occupancy, schema inheritance, array bounds/nulls, invalid depth links, duplicate
recruits, preserved unknown health values, next-game selection, frozen input
reuse, section display, errors, and non-overwriting export.

Pending acceptance, explicitly deferred by the owner:

- Compare the displayed QB depth order with the game.
- Compare the displayed roster injury status with the game.

## Limits

- Injury duration units and active-injury progression are unverified. Values are
  shown as stored, without inferring return dates.
- Individual recruiting fields are schema-derived; board count and total hours
  have UI confirmation. Hidden recruit ratings are not added to the display.
- Null section pointers mean unavailable, not an empty success. Invalid non-null
  references fail loading rather than silently dropping records.
- Other builds, future seasons, postseason transitions, and week advancement need
  separate validation. Unsupported packed layouts are rejected.
- Capturing bytes once prevents mixed sections but is not watcher readiness
  detection. Read while the game is not saving; watcher integration is separate.
- Existing discovery passes repeat in-memory decoding. Consolidation is a future
  performance improvement, not required for correctness of this command.

Next: **Milestone 4 — Local Memory**, preserving observations and history
independently from the current game save.
