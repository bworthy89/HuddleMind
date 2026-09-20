# Milestone 3 roster checkpoint — 2026-09-20

The roster portion is complete for the inspected save/build. Milestone 3 remains active; its broader schedule/results, depth, injury, and recruiting scope is not complete.

## Delivered

- Immutable record, player, team, coach, and snapshot dataclasses.
- Validated report adapter and read-only snapshot loader.
- Controlled-team roster command with position filtering, sorting, aligned output, and expected-error handling.
- JSON export preserving the full snapshot regardless of display filters, with exclusive creation to protect existing files.
- Position counts, highest overall, and arithmetic average overall; display rounding is separate from calculation.
- Forty passing synthetic tests spanning reader boundaries, selection, models/adapters, CLI, export, and summaries.
- Owner confirmation of coach/team identity and selected player positions/ratings against the game, followed by successful direct-save command execution.

The summary export enhancement is deferred in favor of schedule/results discovery. Existing JSON exports contain the snapshot models, not calculated position summaries.

## Remaining limits

The loader still uses research reader internals. Other save builds, complete schema inheritance, and lifecycle stability remain unverified. The watcher is not wired to parsing; stable-file readiness and meaningful-change detection remain Milestone 2 work. Week-advance validation remains deferred. Saved reports and game-derived details stay local.

## Schedule/results discovery started

`bridge/discover_schedule.py` uses validated sequential table traversal, occupied-record checks, and exact team references. It inspects SeasonInfo and SeasonGame fields and retains schema enum labels alongside raw values. Detailed output is kept in ignored `local_data/schedule-discovery.json`.

The first local pass found regular-season fixtures plus a distinct practice record. A completed-status enum was consistent with the stored score ordering; unplayed rows also exist. This is initial evidence, not in-game validation or a general results adapter.

Next: validate season-manager schedule references, distinguish current-season fixtures from templates/history, establish week/year display semantics, and classify completed outcomes using status plus scores. Do not infer byes from missing rows or completed games from nonzero scores alone. A SeasonManager layout currently fails strict whole-word coverage and must be investigated rather than bypassed.

## Schedule reference follow-up

The manager's isolated whole-word SeasonSchedule and SeasonInfo pointers now resolve through checked types, row bounds, and occupancy. This does not relax the general packed-layout check: the manager's method-bearing layout remains unsupported for general decoding. Its occupied schedule array resolves to occupied SeasonGame rows without null or duplicate entries. Team fixtures are intersected with that reference set, and practice records are excluded from the fixture list.

Completed outcomes use the schema's HomeWon/AwayWon/Tied labels and must agree with score ordering. Pending statuses do not become completed merely because scores are present. StatsReported and unfamiliar labels remain unknown. Raw season/week values are preserved; missing weeks are not labeled as byes.

The combined suite now has 46 passing tests, including enum values/aliases, home/away outcome orientation, contradictory scores, and invalid/duplicate schedule references. The detailed fixture report stays local. Next evidence needed is owner comparison of the completed fixture, next opponent, and displayed season/week against the same save. No application schedule model has been added yet.
