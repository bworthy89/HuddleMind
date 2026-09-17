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

## Save safety

Normal bridge operation is read-first. Do not write to or overwrite original CFB27 dynasty files as part of the MVP.
