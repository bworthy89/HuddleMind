# HuddleMind — Project Progress & Learning Tracker

**Repository:** `bworthy89/HuddleMind`  
**Current Phase:** Milestone 3 — Understand the Dynasty (header inspection)

**Current Status:** 🟡 Table-summary rejection tests passed; validation-record checkpoint pending. Week-advance test deferred by owner.

**Last Updated:** 2026-09-19

---

## How to Use This File

This is HuddleMind's living roadmap, learning log, decision record, and short-term task tracker.

Update it whenever we:

- Finish or start a task
- Change architecture
- Learn an important Python concept
- Hit or clear a blocker
- Discover something important about College Football 27
- Add or remove scope

### Status key

- ⬜ Not started
- 🟡 In progress
- ✅ Complete
- 🔴 Blocked
- 🧪 Testing
- ⏸ Paused

---

# 1. Current Focus

## Milestone 0 — Foundation

**Goal:** Establish the repo, documentation, development rules, and a verified local Python environment before feature code begins.

### Completed

- ✅ Project named **HuddleMind**
- ✅ GitHub repository created
- ✅ `PRD.md`
- ✅ `PROJECT_PROGRESS.md`
- ✅ Full project `README.md`
- ✅ Initial repository structure
- ✅ `.gitignore`
- ✅ Secrets / `.env` rules documented
- ✅ Original Python target selected: **3.12**; **3.13.5** verified for current standard-library lessons
- ✅ Dependency approach selected: built-in `venv` + `pip`
- ✅ Development setup documented
- ✅ Initial web-app folder strategy documented
- ✅ Architecture diagram and data flow documented
- ✅ First development workflow documented
- ✅ Bridge learning-first rules documented

### Development PC setup

- ✅ Local project folder opened on the Windows gaming PC
- ✅ Python **3.13.5** confirmed using `python --version`
- ✅ Created and activated `.venv`
- ✅ Verified `sys.executable` points to the project's `.venv\Scripts\python.exe`
- ✅ Ran `bridge/find_dynasty.py` through VS Code and directly with the virtual-environment interpreter
- ✅ Local Git verified; owner output confirms lesson commit `344df29` and successful push to GitHub `main` (`49ba170..344df29`).

The Windows `py` launcher was unavailable, but `python` resolved to an installed interpreter. Python 3.13.5 is accepted for these standard-library lessons; compatibility with future dependencies has not yet been verified. The original setup guide still specifies 3.12.

### Exit criteria

Foundation setup is complete: local Git works and the project virtual environment runs the first bridge script. Remote freshness remains unverified until a fetch.

### Current progress — Lesson 1

The project owner wrote and ran save discovery incrementally. The cleaned-up script uses `find_dynasty_files(save_folder)`, prints modification times, and selects the newest candidate without changing game files. The latest run found 11 candidates and selected `DYNASTY-TULANENEW-AUTOSAVE`. Missing-folder and empty-folder cases passed; the empty-folder case was repeated after the function refactor.

### Immediate next step

Commit the table-summary validation record. Helper-refactor checkpoint `d13e3d2` was pushed successfully according to owner output. Five in-memory rejection tests passed; temporary fixtures were removed and normal table summaries rechecked. Next, inspect Spline field descriptors before attempting target-record decoding. The outer schema is 833.0 and inner schema is 833.1; field semantics remain unverified. The week-advance test remains deferred and Milestone 2 incomplete.

---

# 2. Project Rules

## Python learning rule

HuddleMind is a learning-first Python project.

For Python work:

- The project owner writes instructional Python code.
- Explain each new concept as it appears.
- Build in small runnable increments.
- Inspect output after each meaningful step.
- Debug together rather than replacing code blindly.
- Do not drop large finished implementations by default.
- Boilerplate may be supplied when it has little learning value.
- The project owner can explicitly ask for a full implementation at any time.
- Update the learning log after meaningful lessons.

## Development rule

Prefer the smallest working version first. Add abstraction only after there is a real reason for it.

## Game integration rule

Start read-only.

Preferred order:

1. Save/data reading
2. File watching
3. Screen observation
4. Computer vision
5. HuddleMind-owned historical data
6. Deeper integration only if a proven requirement cannot otherwise be met

## Documentation rule

A feature is not fully complete until relevant documentation is updated.

---

# 3. Milestone Overview

| Milestone | Goal | Status |
|---|---|---:|
| 0 | Foundation | ✅ |
| 1 | Find the Dynasty | ✅ |
| 2 | Watch the Dynasty | 🟡 |
| 3 | Understand the Dynasty | 🟡 |
| 4 | Local Memory | ⬜ |
| 5 | Cloud Bridge | ⬜ |
| 6 | Web Headquarters | ⬜ |
| 7 | Dynasty Brain | ⬜ |
| 8 | Observe the Game | ⬜ |
| 9 | Offensive Coordinator v1 | ⬜ |
| 10 | Adaptive Coordinator | ⬜ |
| 11 | Defensive Coordinator | ⬜ |

---

# 4. Milestone Details

## Milestone 1 — Find the Dynasty

**Status:** ✅ Complete (lesson checkpoint `344df29` pushed)

**Goal:** Use Python to reliably locate CFB27 dynasty save files without modifying them.

### Python learning objectives

- ✅ What a Python script is
- ✅ `import`
- ✅ Variables
- ✅ Strings
- ✅ `pathlib.Path`
- ✅ Objects and methods
- ✅ Boolean values
- ✅ `if` statements
- ✅ Loops
- ✅ Lists
- ✅ Functions — `def`, parameters, calls, and return values
- ✅ Basic error handling — missing-folder guard tested; name, syntax, path-type, capitalization, and indentation bugs debugged

### Tasks

- ✅ Create the first bridge Python file
- ✅ Print the Windows user's home directory
- ✅ Build candidate paths
- ✅ Verify the actual CFB27 folder layout
- ✅ Locate the save directory
- ✅ List files inside it
- ✅ Identify likely dynasty files
- ✅ Print file names and modification times
- ✅ Refactor discovery into a reusable function
- ✅ Add useful missing-folder errors — clear message and clean exit verified by owner output
- ✅ Test discovery against existing local dynasty save candidates (filenames and metadata only; contents not parsed)
- ✅ Collect candidate paths using a list and `append()` — latest run found 11
- ✅ Select the most recently modified candidate using timestamp comparisons
- ✅ Verify empty-result handling with a directory containing no dynasty candidates, including after refactoring
- ✅ Remove obsolete exploratory output and restore the real save path
- ✅ Document the verified save layout

### Verified save layout and observations

On the gaming PC, the observed directory is:

```text
C:\Users\bwort\OneDrive\Documents\EA SPORTS College Football 27\saves
```

The original lesson assumed `%USERPROFILE%\Documents`; the owner subsequently identified OneDrive Documents. Both paths initially showed the same 11 candidates and timestamps. After a normal in-game save, the OneDrive path showed `DYNASTY-TULANENEW-AUTOSAVE` changing from **2026-09-15 19:50:08.465125** to **2026-09-17 09:03:54.998445**, confirming fresh save visibility there. Whether the two paths are linked or separate copies remains unverified. The script now uses the explicit OneDrive path.

The dynasty entries are **files without extensions**, not folders. Candidate filtering uses `item.is_file() and item.name.startswith("DYNASTY-")`. The observed `PROFILE-COLLEGE` file is excluded.

Initial lesson snapshot (superseded by the latest run below):

| Candidate | Observed modification time (PC local time) |
|---|---|
| DYNASTY-JUL10-09h45m31-AUTOSAVE | 2026-07-10 12:12:30.139416 |
| DYNASTY-JUL18-04h38m26-AUTOSAVE | 2026-07-18 16:40:05.929124 |
| DYNASTY-TULANE | 2026-07-18 16:44:31.609134 |
| DYNASTY-TULANE-AUTOSAVE | 2026-07-18 16:44:10.746379 |

The initial run selected **DYNASTY-TULANE**. The latest cleaned-up run found **11 candidates** and selected **DYNASTY-TULANENEW-AUTOSAVE**, modified **2026-09-15 19:50:08.465125**. The prefix filter also includes `DYNASTY-TULANE-AUTOSAVE - Copy`; these are filename candidates, not validated save contents. Newest modification time is not proof of the active in-game dynasty. No save parsing or file watching has been implemented.

Runtime evidence comes from the owner's pasted Windows execution output. Codex reviewed the saved script, including the OneDrive path correction. The original lesson script was committed and pushed as `344df29`; the path correction remains a local change. Codex's own interpreter launch returned access denied, so no independent runtime pass is claimed.

### Exit criteria

HuddleMind can find the configured CFB27 save directory and list candidate dynasty saves without modifying them.

---

## Milestone 2 — Watch the Dynasty

**Goal:** Detect meaningful changes to the active dynasty.

### Learning topics

- Packages and `pip`
- Filesystem events
- Classes
- Callbacks
- Modules
- Logging
- Timestamps
- Long-running processes

### Core tasks

- ✅ Install `watchdog` — owner output confirms version 6.0.0 and successful import
- ✅ Observe modification events at the verified OneDrive save directory
- ✅ Filter directory events and non-`DYNASTY-` filenames; owner confirmed a temporary file and a `DYNASTY-` directory stayed silent
- ✅ Handle creation and rename destinations through shared `queue_change`; create/modify/rename tests and post-refactor debounce passed
- ✅ Debounce per file after one second of quiet; two five-write test bursts each produced one message
- 🟡 Print event metadata; determining meaningful content changes remains unfinished
- ⏸ Actual in-game save detected; week-advance test explicitly deferred by owner
- ✅ Repeated saves, idle operation after the fix, and clean Ctrl+C shutdown verified by owner

### Watcher checkpoint evidence and limitations

`bridge/watch_dynasty.py` uses a handler class, a pending-event dictionary, `time.monotonic()`, and a lock shared with the main polling loop. It prints `st_mtime_ns` and `st_size` after a quiet period. The owner observed an in-game `DYNASTY-TULANENEW-AUTOSAVE` event with timestamp `1789668845088441100` and size `9646981` bytes. Tests are owner-run evidence, not an independent Codex runtime pass.

An initial startup run emitted events for all 11 candidates; a later startup did not repeat that behavior. Cause unknown. No content-change filter or startup suppression was added. Creation, modification, and rename destinations now share `queue_change`. Tests verified an empty file, a temporary-name-to-dynasty rename, a matching-name directory being ignored, and the refactored create/modify/rename sequence (0 bytes, then 27 bytes, then unchanged size/timestamp under the new name). The owner confirmed debounce and a real in-game save again after refactoring; the latter confirmation had no pasted runtime output. Cross-directory moves have not been separately tested. Broader I/O-error recovery and confirmation that a file is ready to parse remain future work.

`FileNotFoundError` recovery is verified with a file deleted during debounce, followed by owner-confirmed processing of a later event. Main-loop cleanup now runs in `finally`; owner output confirmed `Observer alive after cleanup: False` before an intentional `RuntimeError` traceback. The temporary error was removed, normal test-folder operation and Ctrl+C were confirmed again, and the OneDrive path was restored. This cleanup does not cover errors before the main-loop `try` block or all background-thread failures.

`bridge/requirements.txt` records `watchdog==6.0.0`. The local `empty-save-test/` directory is ignored by Git and now contains test files; it must be emptied or replaced before reusing it for a zero-candidate discovery test.

---

## Milestone 3 — Understand the Dynasty

**Goal:** Convert CFB27 data into HuddleMind-owned models.

**Status:** 🟡 Header inspection started; no dynasty entities or compressed payload parsed.

### First header-inspection checkpoint — 2026-09-18 (pushed as `5931dcd`)

The owner wrote `bridge/inspect_save.py` incrementally. It opens the configured autosave in `rb` mode, reads only 64 bytes, checks minimum length and the `FBCHUNKS` signature, and displays hex rows. It decodes a null-padded ASCII field at bytes 34–61 and six little-endian two-byte timestamp components at bytes 22–33, then constructs a timezone-naive `datetime`.

Owner-supplied output confirms:

- File size: 9,646,981 bytes; signature: `FBCHUNKS`.
- Database-name field: `College-27-RL4-9192662`.
- Header timestamp: `2026-09-18 09:03:38`; timezone unverified and distinct from filesystem modification metadata.
- Three-byte `ABC` fixture rejected by the short-file guard, without a traceback.
- A 64-byte `X` fixture passed the length check and was rejected for signature `b'XXXXXXXX'`.
- Real OneDrive autosave path restored; successful decoding repeated after both negative tests.

Field interpretation follows [community CFB27 format research](https://github.com/eric-levinson/cfb27-dynasty-modding/blob/main/docs/save-format.md), accessed 2026-09-18. Its sample identifier is `College-27-RL1-9039126`, differing from this save's RL4 identifier; do not assume all remaining layout details match. The database-name field is not a team name. Header checks do not validate the entire save, and malformed ASCII/date fields or read failures are not yet handled. The initial checkpoint did not decompress data; the subsequent checkpoint below does. Runtime evidence is owner-provided; Codex reviewed the saved source.

### Schema and decompression checkpoint — 2026-09-18 (pushed as `64f8143`)

The inspector now reads an 82-byte header. Four-byte little-endian fields at offsets 62 and 66 report schema **833.0**, unlike the reference schema **809.0**. The field at offset 74 reports **5,864,926** compressed bytes starting at offset **82**, ending exclusively at **5,865,008**, within the 9,646,981-byte file. The prefix at offset 82 is `78 9c`, consistent with zlib.

The owner added exact-length reading, a chunk-range guard, and in-memory decompression using the standard-library `zlib.decompressobj()` with a **64 MiB output cap** (an inspection limit, not a format maximum). Final owner output confirmed:

- Decompressed length: **31,165,754 bytes**.
- `eof`: **True**; `unused_data`: **0 bytes**; `unconsumed_tail`: **0 bytes**.
- Prefix: `b'FrTk\x00\x00\x00\x80\x00\x00\x00\x04\x00\x00\x00\x01'`.
- Explicit complete-stream, trailing/unprocessed-input, and `FrTk` signature checks passed.

This verifies one complete zlib stream exactly occupying the proposed chunk range in this sample. It does not validate the whole save or establish schema 833.0 table/field mappings. No decompressed file was written and no roster entities have been parsed. The new rejection branches (invalid range, short chunk, corrupt/incomplete stream, trailing data, unexpected database signature) are implemented but have not been exercised with negative fixtures. Earlier short/wrong-signature tests used the previous 64-byte header version; do not claim they were rerun after expanding to 82 bytes.

API references checked: [Python zlib documentation](https://docs.python.org/3/library/zlib.html) and [RFC 1950](https://www.rfc-editor.org/info/rfc1950/). Reads currently reopen the live save for separate stages; inspect while the game is not saving. Consistent snapshots, broader I/O handling, and table parsing remain unfinished.

### Initial database table/reference inspection — 2026-09-18 (pushed as `5446e85`)

Owner-run output and incremental source review established the following observations; offsets below are relative to the decompressed database:

- Inner schema fields decode big-endian: major 833 at offset 44, minor 1 at offset 40. Outer schema remains 833.0; the minor-version difference is unresolved. Offset 48 also contains 833 but remains unlabeled.
- Candidate asset-reference area: offset 128, 1,519 eight-byte entries, exclusive end 12,280. The first five references split into table/row pairs `(4318, 0)`, `(6303, 7)`, `(4149, 0)`, `(6351, 0)`, `(6351, 1)` using a 15-bit table ID and 17-bit row number. These targets have not been followed.
- First SPBF marker: 12,428. Subtracting 148 gives candidate table start 12,280, ID 4096. All 128 name bytes are zero; purpose unknown.
- Next SPBF marker: 12,748; table start 12,600; name `OverallPercentage`; ID 4097. Store-name length is 0; BSFT marker check passed; declared record count/capacity are both 22. Record width is two four-byte words (8 bytes) with two field descriptors.
- OverallPercentage descriptor range is `[12832, 12840)`; descriptor values are bit offsets 0 and 32. Candidate record area is `[12840, 13016)`. First three rows as raw unsigned 32-bit pairs: `(678428672, 16)`, `(678428673, 7)`, `(678428674, 12)`.
- Splitting the first raw field as a reference gives table 5176, rows 0–2. An SPBF-only scan found candidate table 5176 named `Spline` at offset 22,009,220. Its BSFT marker check passed, and count/capacity are both 22. Rows 0–2 fit declared capacity, but occupancy and record meanings have not been verified. The second OverallPercentage field is not yet established as a percentage.

Layout references were read from the primary [FranchiseFile implementation](https://github.com/bep713/madden-franchise/blob/master/src/FranchiseFile.js), [reference utilities](https://github.com/bep713/madden-franchise/blob/master/src/services/utilService.js), [table header parser](https://github.com/bep713/madden-franchise/blob/master/src/strategies/common/header/m20/M20TableHeaderStrategy.js), and [field-offset parser](https://github.com/bep713/madden-franchise/blob/master/src/FranchiseFileTable.js). These sources guided the user's Python implementation; no parser package was installed. Descriptor interpretation for this two-field table does not establish a general field decoder.

Limits: scans accept the first matching SPBF candidate, omit alternative table markers, and do not prove all table boundaries, unique IDs, or row occupancy. Bounds checks mostly use the entire decompressed buffer rather than independently verified table extents. Target row contents, schema field names/types, and roster entities remain unparsed. Repeated top-level code should be consolidated incrementally while preserving the known outputs. No new negative-fixture tests or independent Codex runtime pass are claimed.

### Helper refactor checkpoint — 2026-09-18 (pushed as `d13e3d2`)

The owner added `read_u32_be(data, offset)` with an exact four-byte bounds check and `read_table_summary(data, table_start)` returning a dictionary. The table helper checks SPBF/BSFT markers, accounts for variable store-name length, and returns name, ID, store length, record-header position, count, capacity, record words, and field count. Both OverallPercentage and Spline now use it instead of duplicated record-header reads.

Owner output confirms preserved summaries:

- OverallPercentage: ID 4097, store length 0, record-header offset 12,768, count/capacity 22, record words 2, fields 2.
- Spline: ID 5176, store length 21, record-header offset 22,009,409, count/capacity 22, record words 2, fields 3. Eight-byte records do not imply the same two-field layout as OverallPercentage.
- Inner/outer schemas and OverallPercentage raw pairs `(678428672, 16)`, `(678428673, 7)`, `(678428674, 12)` remained unchanged.
- In-memory helper tests: `00 00 03 41` at offset 0 returned 833; offsets -1 and 1 each raised the expected ValueError. Temporary test code was removed; the owner confirmed the final run completed normally afterward. Codex reviewed the final diff and confirmed removal.

Five table-summary rejection cases were subsequently tested on 2026-09-19 (below). The helper remains specific to the inspected SPBF/BSFT layout and does not validate complete table extents, record occupancy, or semantic fields. Helper ValueErrors currently propagate to the caller rather than printing the earlier inline SystemExit messages. No retained automated test suite or independent Codex runtime pass is claimed.

### Table-summary rejection checks — 2026-09-19

Owner output confirms expected ValueErrors for all five in-memory fixtures:

- Negative table start: 168 zero bytes, offset -1.
- Short table header: 167 zero bytes, offset 0.
- Wrong SPBF marker: 168 zero bytes, offset 0.
- Short record header: 168 bytes with SPBF at offsets 148–151.
- Wrong BSFT marker: 224 bytes with SPBF at offsets 148–151, zero store length, and zero-filled BSFT location.

An initial test-list entry omitted its third value (offset 0), causing tuple-unpacking failure before the parser ran; fixing the tuple allowed all five tests to pass. Temporary fixtures and the test loop were removed. The owner then supplied unchanged OverallPercentage and Spline summaries. Codex's final diff review found no functional parser change from `d13e3d2`, only removal of an extra blank line. These are manual test results, not a persistent regression suite; decompression rejection tests and full table/row validation remain unfinished.

### Learning topics

- Dictionaries
- JSON
- Type hints
- Pydantic
- Data validation
- Adapters
- Unit-test fundamentals

### Core tasks

- Evaluate the current parser options
- Parse program identity, roster, schedule, results, depth, injuries, and recruiting where available
- Define HuddleMind-owned models
- Validate parsed data against the game UI
- Add sanitized test fixtures

---

## Milestone 4 — Local Memory

**Goal:** Preserve useful history independently from the current CFB27 save.

### Learning topics

- SQL
- SQLite
- Tables and relationships
- Primary/foreign keys
- CRUD
- Migration concepts

### Core tasks

- Store dynasty identity and observations
- Preserve roster/recruiting/game history
- Store recommendation history
- Survive bridge restarts without losing HuddleMind history

---

## Milestone 5 — Cloud Bridge

**Goal:** Synchronize normalized HuddleMind events to the cloud.

### Learning topics

- Client/server architecture
- HTTP
- REST
- JSON requests
- Authentication basics
- Environment variables
- Retry/error handling
- Async concepts where useful

### Core tasks

- Define bridge registration/authentication
- Define normalized event schema
- Send first real bridge event
- Store it in the cloud
- Add retry/offline queue behavior
- Show bridge online/offline status

---

## Milestone 6 — Web Headquarters

**Goal:** View HuddleMind from a phone or another PC.

### Planned stack

- Next.js
- TypeScript
- Tailwind CSS
- Responsive/mobile-first UI

### Core tasks

- Authentication
- Dynasty selector
- Program dashboard
- Roster
- Schedule
- Recruiting
- Sync status
- Phone and secondary-PC testing

---

## Milestone 7 — Dynasty Brain

**Goal:** Turn data into proactive program recommendations.

### Core tasks

- Position-depth scoring
- Future roster projection
- Recruiting-need scoring
- Recruiting movement alerts
- Injury/development alerts
- Weekly staff report
- Recommendation explanations
- Recommendation history and feedback

---

## Milestone 8 — Observe the Game

**Goal:** Reliably understand core live-game state.

### Learning topics

- Screen capture
- Image arrays
- OpenCV
- Regions of interest
- OCR concepts
- Confidence thresholds
- State machines

### Core state

- Score
- Quarter
- Clock
- Down
- Distance
- Field position
- Possession

### Exit criteria

The second-screen dashboard updates accurately enough to support live recommendations.

---

## Milestone 9 — Offensive Coordinator v1

**Goal:** Recommend useful offensive plays quickly enough for live use.

### Learning topics

- Weighted scoring
- Ranking algorithms
- Basic statistics
- Historical aggregation
- Performance measurement

### Core tasks

- Establish playbook source
- Normalize plays/formations/concepts
- Filter candidate plays
- Score situation fit
- Add clock/field-position logic
- Add user historical success
- Add opponent tendencies
- Add predictability penalty
- Return top three recommendations with explanations
- Track recommendation outcomes

---

## Milestone 10 — Adaptive Coordinator

**Goal:** Personalize live recommendations from accumulated history.

### Core tasks

- User formation/concept tendencies
- Success by situation
- Current-game opponent tendencies
- Tendency-breaking opportunities
- Adaptive weights based on evidence

---

## Milestone 11 — Defensive Coordinator

**Goal:** Add defensive recommendations using opponent behavior.

### Core tasks

- Personnel/formation tendency tracking
- Run/pass tendency
- Target distribution
- QB scramble behavior
- Defensive-call model
- Ranked defensive recommendations
- Outcome evaluation

---

# 5. Learning Log

| Lesson | Topic | Status | What I can now explain / do |
|---|---|---:|---|
| 01 | Paths and files | ✅ | Built paths, discovered candidates, displayed timestamps, and verified missing-folder handling |
| 02 | Conditions, loops, and functions | ✅ | Used conditions, loops, lists, parameters, and return values; verified discovery and empty results after refactoring |
| 03 | File watching and events | 🟡 | Built handler/observer, filtering, locked dictionary, quiet-period debounce, metadata output, and Ctrl+C shutdown; reliability work remains |
| 04 | JSON and dictionaries | ⬜ | Not started |
| 05 | Type hints and Pydantic | ⬜ | Not started |
| 06 | SQLite and SQL | ⬜ | Not started |
| 07 | HTTP and APIs | ⬜ | Not started |
| 08 | Async / realtime concepts | ⬜ | Not started |
| 09 | Computer vision fundamentals | ⬜ | Not started |
| 10 | Statistics and scoring models | ⬜ | Not started |
| 11 | ML fundamentals, if justified | ⬜ | Not started |

### Session notes — 2026-09-16–17

- Built `bridge/find_dynasty.py` incrementally on the Windows gaming PC; the owner typed the instructional Python.
- Practiced imports, variables, strings, `Path.home()`, path joining with `/`, `exists()`, `is_file()`, `is_dir()`, `iterdir()`, and `.name`.
- Practiced indentation, `if/else`, `and`, `startswith()`, loops, empty lists, `append()`, `len()`, zero-based indexing, list truthiness, and `>` comparisons.
- Read metadata with `stat().st_mtime` and converted timestamps using `datetime.fromtimestamp()`.
- Fixed a `NameError` by defining `game_folder` before using it.
- Fixed a `SyntaxError` by separating `print()` arguments with a comma.
- Investigated `NotADirectoryError`: direct filesystem checks confirmed the dynasty save was a file. Corrected reversed File/Folder labels in an `is_file()` branch.
- Implemented `not save_folder.is_dir()` and `raise SystemExit`; missing-folder output confirmed a clear message with no traceback.
- Tested an existing empty directory before and after refactoring; both runs reported zero candidates and no saves.
- Introduced `def`, parameters, function calls, and `return`; separated discovery from timestamp display.
- Fixed case-sensitive `startswith("Dynasty-")` to match `DYNASTY-` filenames.
- Moved `return` outside the loop so every item is checked and empty directories return `[]`.
- Removed exploratory prints and the unused hard-coded save path; restored the real directory and confirmed 11 candidates with newest-save selection.
- Committed and pushed lesson checkpoint `344df29`; installed and imported `watchdog` 6.0.0.
- Corrected the configured path to OneDrive Documents; a controlled in-game save produced a fresh autosave timestamp at that path.
- Built the watcher incrementally; learned classes, inheritance, `self`, callbacks, dictionaries, locks, polling, and elapsed-time comparisons.
- Debugged a missing dictionary assignment and indentation errors around `try`/`except` and the metadata loop; verified idle operation and actual save output afterward.
- Verified two separate event bursts produce one message each and Ctrl+C returns cleanly to PowerShell.
- Startup events across all candidates did not repeat on a later launch; no cause or filtering rule is claimed.
- Pushed basic watcher checkpoint `25f05a7`; added creation/rename handling and verified directory/nonmatching-name filters.
- Refactored event callbacks through `queue_change`; restored an accidentally removed `process_pending_changes` method after an `AttributeError`.
- Verified create/modify/rename metadata, repeated burst grouping, and owner-confirmed real-save operation after restoring the OneDrive path.
- Pushed event-coverage checkpoint `8469844`.
- Verified `FileNotFoundError` handling by creating and deleting a unique test file within the debounce interval; the owner confirmed a later event was still processed.
- Introduced `finally` around the main polling loop; verified Ctrl+C output and intentional `RuntimeError` cleanup with `Observer alive after cleanup: False` before the expected traceback.
- Corrected a misplaced cleanup block inside the metadata loop. Removed the intentional error, restored normal operation, and confirmed another test event and clean Ctrl+C shutdown. Restored the OneDrive path and reviewed the final diff.
- Pushed cleanup checkpoint `c1156fb`.

### Session notes — 2026-09-18

- Added `except OSError as error` after the more specific `FileNotFoundError` handler. Learned exception ordering and binding an exception to a variable without an import.
- A temporary `PermissionError` for one test filename produced the expected diagnostic; another file still produced a normal event. This verifies simulated error handling, not an actual Windows permission-denial scenario.
- Removed the injection and verified normal metadata output for `DYNASTY-ERROR-TEST.txt` (45 bytes).
- Corrected an accidentally duplicated/nested metadata loop and removed an unnecessary `from dbm import error` import. Reviewed the final diff: only the OSError handler remains as a functional change.
- Restored the OneDrive path; the owner confirmed a final real-save event and clean shutdown after the structural corrections. This confirmation had no pasted runtime output.
- Failed metadata reads are reported and skipped. Automatic retry, file-readiness detection, and meaningful content-change detection remain unimplemented.
- Pushed metadata error-handling checkpoint `146e774`; owner deferred the week-advance test.
- Began binary inspection: learned `rb`, bounded reads, byte slices, hex output, null-terminated ASCII decoding, little-endian integers, and `datetime` construction.
- Verified real-header decoding and short-file/wrong-signature rejection, then restored and reran the real save. See Milestone 3 for values and source attribution.
- Pushed header-inspection checkpoint `5931dcd`.
- Learned `seek`, four-byte little-endian decoding, chunk bounds, bounded zlib decompression, stream completion, and trailing/unprocessed input checks. Verified schema 833.0 and a complete stream yielding a `FrTk` prefix; see the decompression checkpoint above.
- Pushed decompression checkpoint `64f8143`.
- Practiced big-endian decoding, absolute/relative offsets, `divmod`, reference bit allocation, `find`, `break`, `None`, and field descriptors. Inspected OverallPercentage raw rows and a candidate link to Spline, preserving uncertainty about semantics and row occupancy.
- Fixed a missing comma in a multiline print and restored the raw-record layout guard's `raise SystemExit`.
- Pushed table-inspection checkpoint `5446e85`.
- Introduced bounded integer reads, reusable table-summary parsing, and dictionaries as multi-value function results; replaced duplicate OverallPercentage/Spline record-header sections.
- Verified unchanged metadata/raw rows and valid/invalid integer-helper offsets; removed temporary test code and confirmed normal operation again.
- Helper refactor was subsequently pushed as `d13e3d2`.

### Session notes — 2026-09-19

- Practiced `bytes`, mutable `bytearray`, tuple unpacking, and `try`/`except`/`else` with five invalid table-summary fixtures.
- Fixed a two-value test tuple where the loop expected three values; all five rejection tests then produced the expected messages.
- Removed temporary fixtures and confirmed unchanged real-save table summaries. No functional parser changes remain relative to the pushed helper refactor.
- Next: commit validation notes, then inspect Spline's three field descriptors without assuming OverallPercentage's two-field layout.

### Lesson notes template

```text
## Lesson XX — Title

Date:
Feature:

What we built:

New concepts:

What I understand now:

What confused me:

Bugs we hit:

How we fixed them:

Code I want to revisit:

Next lesson:
```

---

# 6. Architecture Decisions

## ADR-001 — Web-first product

**Accepted:** 2026-09-16

The main HuddleMind interface is a responsive web application. A lightweight Windows bridge runs on the CFB27 PC.

## ADR-002 — Python powers the bridge

**Accepted:** 2026-09-16

Python handles local CFB27 integration, data processing, computer vision, analytics, and recommendation logic where practical.

## ADR-003 — Python is taught, not merely generated

**Accepted:** 2026-09-16

Instructional Python code is developed incrementally by the project owner with guided explanation and debugging.

## ADR-004 — CFB27 integration starts read-only

**Accepted:** 2026-09-16

Initial versions observe saves/data and game visuals without modifying original dynasty saves or injecting into the game process.

## ADR-005 — Normalize before cloud sync

**Accepted:** 2026-09-16

The bridge converts CFB27-specific information into HuddleMind-owned models/events before synchronization.

## ADR-006 — Fast deterministic live engine first

**Accepted:** 2026-09-16

Live play ranking begins with explicit scoring/statistical logic. LLMs can explain recommendations but do not sit in the time-critical path.

## ADR-007 — Beginner-transparent Python environment

**Accepted:** 2026-09-16

Originally selected Python 3.12, built-in `venv`, and `pip`. During the first lesson, Python **3.13.5** was available on the gaming PC and was verified inside the project virtual environment. Continue with 3.13.5 for the standard-library lessons; revisit compatibility before adding third-party dependencies. Add more advanced dependency tooling only when it solves a real problem.

---

# 7. Research / Unknowns

| Question | Status | Notes |
|---|---:|---|
| Exact CFB27 dynasty save location/naming on this PC | ✅ | OneDrive Documents/EA SPORTS College Football 27/saves; fresh autosave observed after in-game save; see Milestone 1 |
| Best current CFB27 parser foundation | ⬜ | Evaluate before Milestone 3 |
| Which dynasty entities are reliably available | ⬜ | Validate against real save |
| Recruiting data completeness | ⬜ | Validate |
| Facilities/staff data completeness | ⬜ | Validate |
| Reliable playbook extraction method | ⬜ | Needed before live coordinator |
| Can selected plays be detected visually? | ⬜ | Prototype later |
| Best scoreboard recognition approach | ⬜ | Milestone 8 |
| UI scale/resolution impact on recognition | ⬜ | Test later |
| Final Supabase/backend responsibility split | ⬜ | Decide after local bridge prototype |

---

# 8. Blockers

No active product blockers.

**Verified:** Python 3.13.5 virtual environment runs the bridge script on the Windows PC.

**Pending:** commit the table-summary validation record. Week-advance testing is deferred by owner. Decompression negative tests, watcher retries, meaningful-change detection, consistent save snapshots, and full database parsing remain unfinished. Checkpoints through `d13e3d2` were successfully pushed according to owner output.

---

# 9. Product Backlog

- ⬜ PWA install experience
- ⬜ Push notifications for important dynasty alerts
- ⬜ Voice coordinator mode
- ⬜ Compare seasons
- ⬜ Compare multiple dynasties
- ⬜ Recruiting class grading
- ⬜ Scheme-fit ratings
- ⬜ Player-development projections
- ⬜ Transfer/departure risk modeling if data allows
- ⬜ Automated opponent scouting report
- ⬜ Drive-by-drive summary
- ⬜ Halftime adjustment report
- ⬜ Postgame coordinator grade
- ⬜ Fourth-down decision model
- ⬜ Clock-management assistant
- ⬜ Two-minute drill mode
- ⬜ Red-zone recommendations
- ⬜ Tendency heatmaps
- ⬜ Historical coaching profile
- ⬜ Ask HuddleMind conversational assistant
- ⬜ Local-model support
- ⬜ Exportable season report

---

# 10. Change Log

## 2026-09-19

- Recorded helper-refactor checkpoint `d13e3d2` as pushed, five successful table-summary rejection cases, and restored normal inspection after removing test fixtures.

## 2026-09-18

- Refactored integer/table-header reads into reusable functions, verified preserved outputs and integer bounds checks, and recorded `5446e85` as pushed.
- Recorded inner/outer schema difference, asset-reference samples, OverallPercentage layout/raw rows, and a capacity-checked Spline target candidate. Decompression checkpoint `64f8143` was pushed.
- Verified schema 833.0, exact chunk bounds, and complete bounded decompression to 31,165,754 bytes beginning with `FrTk`; recorded remaining validation limits.
- Started Milestone 3 after the owner deferred week-advance testing; recorded read-only header decoding and both guard tests.
- Recorded metadata error-handling checkpoint `146e774` as pushed.
- Added report-and-skip handling for metadata OSError failures; recorded simulated permission-error recovery and restored normal operation.
- Recorded cleanup checkpoint `c1156fb` as pushed and the remaining limits around retries and meaningful changes.

## 2026-09-17

- Recorded verified Windows Python 3.13.5 virtual environment and successful script execution.
- Updated Milestone 1 and learning objectives from observed lesson output.
- Documented the verified save path, extensionless dynasty files, four candidates, and newest-file selection.
- Completed missing-folder and empty-folder checks using owner-supplied execution output.
- Reviewed the function refactor and cleaned-up script; recorded capitalization and return-indentation debugging lessons.
- Recorded the latest 11-candidate run and newest save; marked Foundation and Find the Dynasty complete.
- Verified local Git and recorded owner-confirmed commit/push of `344df29`.
- Recorded `watchdog` 6.0.0 installation/import and the OneDrive save-path correction, validated by a fresh in-game autosave timestamp.
- Recorded the verified watcher checkpoint, burst tests, clean shutdown, metadata output, and unresolved startup-event behavior; added the dependency record and ignored local test files.

## 2026-09-16

### Added / established

- Selected **HuddleMind** as the project name.
- Created product PRD and progress tracker.
- Expanded root project README.
- Added initial `bridge/`, `web/`, and `docs/` structure.
- Added `.gitignore` covering Python, Node, secrets, local databases, captures, logs, and editor files.
- Added architecture documentation and Mermaid system diagram.
- Added local development/setup guide.
- Selected Python 3.12 + `venv` + `pip` for the initial bridge environment.
- Established secrets and local-game-data rules.
- Established Python learning-first development rule.
- Established read-only-first CFB27 integration strategy.
- Established fast-brain / deep-brain recommendation split.

---

# 11. Next Session — Understand the Dynasty

1. Review and commit the explicit checkpoint files; do not stage local test data.
2. Inspect Spline's three field descriptors using the shared summary, then determine record bit layout before decoding target rows.
3. Add appropriate handling for malformed decoded fields as inspection becomes reusable.
4. Keep week-advance testing deferred until the owner resumes it. Watcher retry, lifecycle, cross-directory events, and meaningful-change filtering remain separate unfinished work.

Continue the learning-first workflow: the owner writes small Python increments, runs them, and shares output before the next step.
