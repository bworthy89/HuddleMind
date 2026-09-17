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

For that reason, this directory intentionally contains **no finished Python implementation yet**.

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

Target Python version: **3.12**

Initial environment tooling:

- `venv`
- `pip`

See [`../docs/DEVELOPMENT.md`](../docs/DEVELOPMENT.md) for setup instructions.

## Important Constraint

Normal bridge operation is read-first. Do not write to or overwrite original CFB27 dynasty files as part of the MVP.
