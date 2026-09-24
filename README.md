# HuddleMind

HuddleMind is an AI-powered companion platform for **College Football 27 on PC**. A lightweight Windows bridge observes dynasty and live-game information, converts it into HuddleMind-owned data, and syncs it to a responsive web app that can be viewed from a phone, tablet, laptop, or second PC.

The project has two major goals:

1. **Dynasty Intelligence** — help with recruiting, roster construction, depth, injuries, development, staff/facilities decisions, opponent preparation, and other long-term program decisions.
2. **Live Coordinator** — provide fast, context-aware play-call suggestions based on the current game situation, the user's history, and opponent tendencies.

> HuddleMind is being built as both a real product and a hands-on Python learning project. Python features are developed step by step so the code is understood, not merely generated.

## Current Status

**Phase:** Milestone 5 — Cloud Bridge (hosted delivery and automatic capture)

**Status:** The HTTPS receiver is deployed, daily backups verify isolated restoration, and Windows retries queued delivery every five minutes. The capture watcher validates stable save bytes and atomically stores an observation and its sync event. Authenticated bridge health now reports sender connectivity, capture activity, queue count, successful capture/delivery times, and errors. Run `.\bridge\send_hosted.ps1 -HealthOnly` to read it. All 227 tests pass. A fresh in-game save still needs final acceptance. See [operations](deploy/OPERATIONS.md) for launch, scheduling, and recovery instructions and [Local Memory](docs/LOCAL_MEMORY.md) for history. Final depth-chart and injury UI checks remain deferred as recorded in [Milestone 3](docs/MILESTONE_3_CHECKPOINT.md).

Run `python -m bridge.show_dynasty "PATH_TO_SAVE" "PATH_TO_SCHEMA.gz"` from the project root. Add `--section depth`, `--section health`, `--section recruiting`, or `--section all`. Add `--export "local_data/dynasty-full.json"` to create a new complete export; existing files are protected.

Run `.\bridge\watch_hosted.ps1` to watch the configured Tulane autosave while playing. Keep its terminal open; Ctrl+C stops capture. This polls one selected save and leaves network delivery to the scheduled sender. Broader lifecycle validation, capture startup at logon, and the web app remain future work. The inspector notes below describe the earlier exploratory script; the current application uses the validated reader modules.

See [`PROJECT_PROGRESS.md`](./PROJECT_PROGRESS.md) for the live roadmap and learning tracker.

`bridge/inspect_save.py` reads an 82-byte header and decodes the database-name field, timestamp, schema, and chunk size. Owner-run checks verified a complete zlib stream decompressing in memory to 31,165,754 bytes beginning with `FrTk`, under a 64 MiB cap. Earlier header guard tests passed; expanded decompression rejection branches remain untested. It does not yet parse dynasty entities or validate the full save format.

The exploratory inspector distinguishes outer schema 833.0 from inner 833.1 and follows candidate references from `OverallPercentage` through `Spline` to an `int[]` table with ASTO/CMPC markers. Locally exported schema definitions identify position fields and Spline X/Y references. Three sampled Splines retrieve their arrays through stored references, each producing 11 paired points with strictly increasing X values. An unloaded-row check passed; different-table and unequal-length branches remain untested. Full schema compatibility, integer-branch applicability, row occupancy, interpolation, and gameplay meaning remain unverified. See the progress tracker for exact evidence and limits.

## Architecture

```text
College Football 27 (Gaming PC)
            |
            v
HuddleMind Windows Bridge
Python / read-first integration
            |
            | normalized HTTPS / realtime events
            v
HuddleMind Cloud
Database + API + realtime + AI services
            |
            v
HuddleMind Web App
Phone / tablet / browser / second PC
```

The bridge is the only component that needs local access to College Football 27. The web app is the primary user interface.

For the full design, see [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md).

## Repository Structure

```text
HuddleMind/
├── bridge/                 # Windows bridge; Python learning-first development
├── web/                    # Responsive web application
├── docs/                   # Architecture and development documentation
├── PRD.md                  # Product requirements
├── PROJECT_PROGRESS.md     # Roadmap, learning log, decisions, backlog
├── .gitignore
└── README.md
```

Additional folders will be added only when the project actually needs them.

## Development Principles

- **Read first.** Observe CFB27 before considering invasive integration.
- **Normalize game data.** The web app should depend on HuddleMind models, not raw CFB27 internals.
- **Fast brain + deep brain.** Live play calling uses fast deterministic/statistical logic; AI models handle deeper analysis and explanations.
- **Explain recommendations.** HuddleMind should show why it recommended an action.
- **Learn the user.** Recommendations should become more personalized as history accumulates.
- **Build small.** Create the smallest useful working version before adding abstraction.
- **Learn Python by building.** Instructional Python code is written incrementally by the project owner with guided explanation.

## Python Environment

The original Python target was **3.12**; the current standard-library lessons run in a verified **Python 3.13.5** virtual environment. Check compatibility before adding third-party dependencies.

For the first learning stages, HuddleMind uses Python's built-in `venv` plus `pip`. This keeps the environment transparent while the fundamentals are being learned. More advanced tooling can be introduced later if it solves a real project problem.

Local setup instructions live in [`docs/DEVELOPMENT.md`](./docs/DEVELOPMENT.md).

## First Development Milestone

The first real coding milestone is intentionally small:

> Use Python to locate the College Football 27 save directory and identify candidate dynasty saves without modifying anything.

This teaches the foundation we will later use for save watching, parsing, synchronization, and the live bridge.

See [`bridge/README.md`](./bridge/README.md).

## Product Documentation

- [`PRD.md`](./PRD.md) — product requirements and long-term vision
- [`PROJECT_PROGRESS.md`](./PROJECT_PROGRESS.md) — milestones, learning progress, decisions, blockers, and backlog
- [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md) — technical architecture and data flow
- [`docs/DEVELOPMENT.md`](./docs/DEVELOPMENT.md) — development workflow and local setup

## Project Scope Notes

The MVP is focused on **offline/read-first College Football 27 PC dynasty workflows**. HuddleMind should not modify original dynasty saves during normal operation.

Game-specific assumptions are treated as research questions until verified against the user's actual installation and save data.
