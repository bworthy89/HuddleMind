# HuddleMind Bridge

The bridge is the Windows-side component that connects College Football 27 to HuddleMind.

It will eventually handle:

- Finding dynasty saves/data
- Detecting changes
- Parsing/normalizing CFB27 information
- Maintaining local state
- Sending normalized events to the cloud
- Observing live games
- Running fast recommendation logic

## Learning-First Rule

The bridge is also the main Python learning area for HuddleMind.

Instructional Python code should be written by the project owner in small steps with explanation and debugging along the way.

The first lesson script, `find_dynasty.py`, was written incrementally by the owner. It discovers `DYNASTY-` candidate files, displays timestamps, and selects the newest file without modifying saves. Normal, missing-folder, and empty-folder behavior have been verified through owner-supplied execution output.

## First Lesson

### Lesson 1 — Find the Dynasty

Goal:

> Write a small Python program that discovers the Windows user's home directory, investigates likely CFB27 data locations, and eventually lists candidate dynasty saves.

Concepts we will learn:

- `import`
- Variables
- Strings
- `pathlib.Path`
- Objects and methods
- Path construction
- Boolean values
- `if` statements
- Loops
- Lists
- Functions
- Basic error handling

We will introduce these incrementally rather than all at once.

## Planned Progression

```text
Lesson 1  Paths and files
Lesson 2  Conditions, loops, and functions
Lesson 3  File watching and events
Lesson 4  JSON and structured data
Lesson 5  Type hints and validated models
Lesson 6  SQLite and persistence
Lesson 7  HTTP / cloud synchronization
Lesson 8  Realtime concepts
Lesson 9  Computer vision
Lesson 10 Statistics and recommendation scoring
Lesson 11 ML only if real data justifies it
```

## Environment

Current lesson environment: **Python 3.13.5** (original target: 3.12; dependency compatibility will be checked before adding packages).

Initial environment tooling:

- `venv`
- `pip`

See [`../docs/DEVELOPMENT.md`](../docs/DEVELOPMENT.md) for setup instructions.

## Watcher checkpoint

Install the recorded dependency from the repository root using the active virtual environment:

```powershell
python -m pip install -r bridge/requirements.txt
python bridge/watch_dynasty.py
```

Both scripts currently use this PC's explicit OneDrive save path. Adjust it before running on another machine. The watcher handles creation, modification, and rename destinations for `DYNASTY-` filenames through a shared queue helper, ignores directory events, and groups events per path after one second of quiet. It prints modification time in nanoseconds and size in bytes. Ctrl+C stops it.

Owner-run checks verified repeated saves, burst grouping, idle operation, clean Ctrl+C shutdown, and an actual in-game autosave. Further checks verified creation, rename destinations, temporary-name filtering, and directory filtering. Create/modify/rename and debounce tests passed after the shared-helper refactor; the owner also confirmed another real-save check. An initial startup burst did not repeat; its cause remains unknown. Events and metadata do not prove a content change or that a save is ready to parse. Broader file-access recovery and cross-directory move testing remain unfinished.

For controlled tests, create `empty-save-test` in the repository root and temporarily point `watch_folder` there. The directory is ignored by Git. Use ordinary test files there; restore the real path after testing.

## Read-only header inspector

Run `python bridge/inspect_save.py` from the project root while the game is not actively saving. The script currently points to this PC's OneDrive `DYNASTY-TULANENEW-AUTOSAVE`; adjust that assignment for another file. It reads an 82-byte header, checks length and signature, and decodes the database-name field, timestamp, schema version, and proposed chunk size. The observed identifier is `College-27-RL4-9192662`, schema is **833.0**, and timestamp timezone is unknown.

It reads the proposed chunk and decompresses it in memory with a 64 MiB output cap, checking complete stream consumption and the `FrTk` signature. Owner output verified 5,864,926 compressed bytes at offset 82 yielding 31,165,754 bytes with no trailing or unprocessed input. No output file is written. Error branches for the expanded chunk inspection have not yet been tested with negative fixtures. Reads reopen the live save; consistent snapshots remain future work.

Offsets follow [community CFB27 format research](https://github.com/eric-levinson/cfb27-dynasty-modding/blob/main/docs/save-format.md), with fields checked against owner output. The reference uses a different RL1 identifier. This is an initial inspector, not a full save validator or dynasty parser; malformed text/date values and read failures are not yet handled. Owner-run tests verified the real save, a three-byte input, a 64-byte wrong-signature input, and restoration of the real path. Test fixtures stay in the ignored local test directory.

## Exploratory database inspection

The inspector also displays the decompressed header, inner schema 833.1 (outer 833.0), sample asset-reference entries, and SPBF table candidates. Owner output confirms an unnamed ID-4096 candidate, `OverallPercentage` ID 4097 with 22 eight-byte records and two descriptors, and candidate references from its first three rows to `Spline` ID 5176. The Spline BSFT check and capacity check pass, but no target records or semantic field meanings have been decoded. Searches currently use SPBF only and accept the first ID match. This is an exploratory script, not a complete table index or general field decoder.

Integer reads and repeated record-header inspection now use `read_u32_be` and `read_table_summary`. The latter returns a dictionary and checks SPBF/BSFT markers plus buffer bounds. Owner-run comparisons preserved both table summaries and raw OverallPercentage rows; integer-helper negative/short reads were rejected. Spline has 21 store-name bytes and three fields, while OverallPercentage has zero and two. Five manual in-memory tests rejected a negative start, short table header, wrong SPBF marker, short record header, and wrong BSFT marker. Temporary test code was removed and both real-save summaries remained unchanged. These tests are not retained as a regression suite; exceptions propagate to the caller.

## Save safety

Normal bridge operation is read-first. Do not write to or overwrite original CFB27 dynasty files as part of the MVP.
