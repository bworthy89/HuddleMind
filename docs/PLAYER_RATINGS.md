# Saved player ratings

The Player schema in the local CFB27 833.0 bundle contains 56 allowlisted integer
rating fields beyond overall. Each declares a range of 0–127. Discovery reads
them using the same checked packed-field layout as position and overall; schema
names are retained in immutable `PlayerRating(field, value)` objects. Missing
fields become null. Unexpected types/ranges and invalid values fail explicitly.
Enums such as prospect star quality and running style are not rating integers.

Groups cover physical/mental, passing, ball carrying, receiving, blocking,
defense, and special teams. `bridge/player_ratings.py` lists exact source names.
The web player detail view labels these **saved ratings**. We have not established
that they equal unmodified base ratings or the game's temporarily boosted display.
No modifier arithmetic or rating clamps are applied.

## Evidence and limits

On 2026-09-24 a read-only local save check resolved all allowlisted fields for
the controlled roster. Individual player names and values remain local.
These are parser observations, not in-game visual confirmation. No game files or
existing observations were altered. Comparison with the in-game ratings screen
and understanding temporary modifiers remain pending.

## Compatibility and rollout

`ratings` is an additive optional Player member within event schema v1. The updated
receiver accepts legacy Player objects without it without mutating their JSON;
new entries are shape/range/allowlist/duplicate validated. Deploy the updated
receiver before delivering enriched events. Old receivers reject the new field.

Exports, SQLite snapshots, outbox events and delivery preserve ratings through
dataclass serialization. Existing save/schema pairs stay deduplicated and immutable:
rerunning capture on an already stored pair does not retrofit its old payload.
Restart an already running capture watcher to load the new code, then capture a
new in-game save when ready. Existing hosted snapshots show ratings unavailable
until an enriched observation arrives. No fresh in-game save test was performed.

Verification: 236 Python tests, 13 web tests, production build and HTTP smoke
checks passed. Mobile synthetic UI review confirmed zero/127 values, missing
attribute labels, expandable groups, and visible bottom navigation.
