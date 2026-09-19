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

The inspector displays the decompressed header, inner schema 833.1 (outer 833.0), sample asset references, and table candidates. Owner output confirms `OverallPercentage` ID 4097 with 22 eight-byte records and two descriptors, and candidate references to `Spline` ID 5176. Spline descriptor values are 32, 32, 0; its first three rows contain raw slots that split into references to table 4722, rows (1, 0), (3, 2), and (5, 4).

SPBF-only scanning missed table 4722. A separate ASTO/SPEX search found an ASTO candidate named `int[]`, with a CMPC record-section marker. Candidate count/capacity are 44 and width is 11 words. The proposed array record range fits the database, and its first six preceding entries each contain 11. Six sampled records contain raw u32 values slightly above `2 ** 31`; subtracting that amount yields alternating increasing/decreasing sequences. Element-count interpretation, integer encoding, curve axes, field meanings, and occupancy remain unverified. Marker scans do not establish unique valid tables. This remains an exploratory script, not a complete table index or general field decoder.

Integer reads and repeated record-header inspection now use `read_u32_be` and `read_table_summary`. The latter returns a dictionary and checks SPBF/BSFT markers plus buffer bounds. Owner-run comparisons preserved both table summaries and raw OverallPercentage rows; integer-helper negative/short reads were rejected. Spline has 21 store-name bytes and three fields, while OverallPercentage has zero and two. Five manual in-memory tests rejected a negative start, short table header, wrong SPBF marker, short record header, and wrong BSFT marker. Temporary test code was removed and both real-save summaries remained unchanged. These tests are not retained as a regression suite; exceptions propagate to the caller.

## Schema-backed Spline inspection

The owner exported revision-4 OverallPercentage, Spline, PositionE, and Spline_CalculateY FTX definitions from MMC Frosty to `E:\aibridgemod`, outside this repository. These identify OverallPercentage's PercentageSpline and PlayerPosition fields; position values 16, 7, 12 correspond to CB, C, DT. Spline declares a final CalculateY member and X/Y int[] references. Descriptor rules map Y to the first four-byte slot and X to the second. Owner output confirms X/Y row pairs (0, 1), (2, 3), (4, 5) in table 4722. This advances the earlier unnamed-slot investigation; complete schema compatibility remains unverified.

`decode_candidate_int_array_value` preserves raw zero and otherwise subtracts `2 ** 31`, following a conditional branch in the reference parser. Four manual zero/bias-boundary checks passed, temporary checks were removed, and all six sampled arrays remained unchanged after helper integration. Its range-rejection cases have not been tested; applicability of this decoding branch still depends on integer metadata.

Decoded samples are stored by array row number; a separate dictionary retains each sampled Spline's X/Y table and row references. Pairing now follows those references, checks target table IDs and loaded-row availability, and checks equal lengths before zip. Owner output confirms 11 points with increasing X values for each of three Splines. Temporarily loading only two array rows exercised the unloaded-row guard; the six-row sample was restored and normal operation confirmed. Different-table and unequal-length branches remain untested. Loading is still limited to the first six array rows, not a general on-demand reader. CalculateY's schema declares an integer expression taking xValue in 0–100, but contains no calculation implementation. Interpolation, gameplay meaning, and occupancy remain unresolved. Validation is owner-run output, not a retained automated test suite.

## Position-linked curve summaries

`overall_links` preserves each sampled OverallPercentage record's raw position and full Spline reference. Curve summaries match both table ID and row number. Labels now load through ElementTree from the required local export `E:\aibridgemod\positionE.FTX`; adjust that path on another PC. The file is outside the repository. All enum names are grouped by stored integer value, preserving aliases; a label is selected only when exactly one name lacks a trailing underscore. Other values retain the unknown-value fallback.

The XML path now calls three helpers: `read_position_members`, `group_position_names`, and `build_position_labels`. Owner output confirms 71 members, preserved aliases, and unchanged CB/C/DT curve summaries after refactoring. Earlier root/revision/declared-count diagnostics were removed; metadata is not enforced. The local export was previously observed at revision 4.

Manual label-helper checks passed for one eligible name, a marker-only group, and two competing display names; only the first produces a label. Member grouping now rejects missing/empty/whitespace-only names and catches missing/empty/nonnumeric integer values with a member-specific error and chained cause. All six invalid-member checks passed using in-memory XML. Temporary test code was removed and normal output rechecked. Missing-enum and file/XML error cases remain untested; root/count/version and numeric-range validation remain incomplete. Shared-Spline and no-sampled-link cases also remain untested.

## Schema-loading errors

The XML reader's caller catches missing files and malformed XML, reports the path (plus the XML parser reason when available), and exits with SystemExit(1). Owner-run tests confirmed both messages using a nonexistent path and a separate incomplete-XML fixture in the ignored test folder. The real export path was restored and normal output confirmed. Exit-code behavior is explicit in source but was not separately measured in the shell. Missing-enum/member-validation errors and other file-access exceptions still propagate; full schema validation remains unfinished.

The caller also catches the XML reader's ValueError for missing PositionE, reports the path and reason, and exits with code 1. Focused execution of the actual helper/caller block passed missing-enum and wrong-enum checks, malformed-XML regression, and real-export loading (71 members). These checks used in-memory fixtures and did not run the full save pipeline. Later member-grouping errors remain outside this handler, and other OSErrors still propagate.

Schema error reporting now surrounds reading, member grouping, and label selection together. FileNotFoundError retains its specific message; other OSErrors report the path and reason; XML syntax and schema/member ValueErrors have distinct messages. All stop with exit code 1. Eleven focused tests of the actual helper/caller code passed, including simulated I/O failures and six invalid-member inputs; the real export still yields 71 members and correct CB/C/DT labels. These are focused checks, not a full save-pipeline run or complete schema-format validation. This supersedes the earlier limitations on uncaught member and file-access errors. Next: explore beyond the fixed three-Spline/six-array sample by following references.

## Expanded reference exploration

OverallPercentage inspection now collects all 22 declared source records. Referenced Spline and array row numbers are deduplicated and checked against the selected table IDs and declared ranges before reading. Owner output confirms 22 requested Splines, 44 requested arrays, and 22 completed pairings; extended QB/TE/WR examples retain 11 points and increasing X values. This supersedes the earlier three-Spline/six-array sample limits. Coverage does not prove occupancy or gameplay semantics, and table discovery remains exploratory. Next work moves to exported Team/Player schemas and actual dynasty records rather than further curve-summary refinement.

## Save safety

Normal bridge operation is read-first. Do not write to or overwrite original CFB27 dynasty files as part of the MVP.
