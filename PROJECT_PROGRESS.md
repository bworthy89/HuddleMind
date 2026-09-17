# HuddleMind — Project Progress & Learning Tracker

**Repository:** `bworthy89/HuddleMind`  
**Current Phase:** Milestone 0 — Foundation  
**Current Status:** 🟡 In Progress  
**Last Updated:** 2026-09-16

---

## How to Use This File

This is the living project tracker for HuddleMind.

Update it whenever we:

- Finish a task
- Start a new task
- Change architecture
- Learn an important Python concept
- Hit a blocker
- Make a product decision
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

## Active milestone

### Milestone 0 — Foundation

**Goal:** Establish the project, documentation, development rules, and environment before writing feature code.

Current priority:

1. Finalize project documentation.
2. Establish repo structure.
3. Set up the Python development environment.
4. Begin Lesson 1: locating the CFB27 save directory with Python.

---

# 2. Project Rules

## Python learning rule

HuddleMind is a learning-first Python project.

For Python work:

- The user writes the instructional Python code.
- Each concept is explained before or while it is introduced.
- Features are built in small steps that can be run and understood.
- Debugging is done together.
- Finished large Python implementations are not dropped in by default.
- Boilerplate may be provided when it has little learning value.
- The user may explicitly ask for a complete implementation at any time.
- New Python concepts should be recorded in the Learning Log below.

## Development rule

Prefer the smallest working version first.

Before adding abstraction, ask:

> Do we have enough repetition or complexity to justify this yet?

## Game integration rule

Start read-only.

Prefer:

1. Save/data reading
2. File watching
3. Screen observation
4. Computer vision
5. HuddleMind-owned history

Avoid invasive integration unless later evidence proves it is necessary.

## Documentation rule

A feature is not fully complete until its relevant documentation is updated.

---

# 3. Milestone Tracker

## Milestone 0 — Foundation

**Status:** 🟡 In Progress

- ✅ Select project name: **HuddleMind**
- ✅ Create GitHub repository
- ✅ Create `PRD.md`
- ✅ Create `PROJECT_PROGRESS.md`
- ⬜ Create project `README.md`
- ⬜ Define initial repository structure
- ⬜ Create `.gitignore`
- ⬜ Establish secrets / `.env` rules
- ⬜ Select supported Python version
- ⬜ Create Python virtual environment
- ⬜ Add dependency-management approach
- ⬜ Add development setup instructions
- ⬜ Decide initial web-app folder structure
- ⬜ Create architecture diagram in docs
- ⬜ Document first development workflow

### Exit criteria

Milestone 0 is complete when a fresh machine can clone the repository and follow documented steps to reach a working development environment.

---

## Milestone 1 — Find the Dynasty

**Status:** ⬜ Not Started

**Goal:** Use Python to reliably locate CFB27 dynasty save files.

### Python learning objectives

- ⬜ What Python scripts are
- ⬜ Imports
- ⬜ Variables
- ⬜ Strings
- ⬜ `pathlib.Path`
- ⬜ Objects and methods
- ⬜ Boolean values
- ⬜ `if` statements
- ⬜ Loops
- ⬜ Lists
- ⬜ Functions
- ⬜ Basic error handling

### Tasks

- ⬜ Create the bridge Python project
- ⬜ Print the user's home directory
- ⬜ Build the expected Documents path
- ⬜ Locate the CFB27 save folder
- ⬜ Check whether the folder exists
- ⬜ List files inside the folder
- ⬜ Identify likely dynasty files
- ⬜ Print file names and modification timestamps
- ⬜ Turn file discovery into a reusable function
- ⬜ Add useful error messages
- ⬜ Test with a real CFB27 dynasty save
- ⬜ Document the discovered save layout

### Exit criteria

Given the user's Windows machine, HuddleMind can find the configured CFB27 save directory and list candidate dynasty saves without modifying them.

---

## Milestone 2 — Watch the Dynasty

**Status:** ⬜ Not Started

**Goal:** Detect when the selected dynasty changes.

### Python learning objectives

- ⬜ Installing packages
- ⬜ `pip`
- ⬜ Virtual environments
- ⬜ Classes
- ⬜ Events / callbacks
- ⬜ Modules
- ⬜ Logging
- ⬜ Timestamps
- ⬜ Long-running Python processes

### Tasks

- ⬜ Install and understand `watchdog`
- ⬜ Watch the save directory
- ⬜ Detect file changes
- ⬜ Filter unrelated file-system events
- ⬜ Add structured logging
- ⬜ Associate a changed file with a dynasty
- ⬜ Avoid duplicate rapid-fire events
- ⬜ Create bridge start/stop behavior
- ⬜ Record detected events locally
- ⬜ Test while advancing a real dynasty

### Exit criteria

HuddleMind reports a clean, meaningful event when the active dynasty save changes.

---

## Milestone 3 — Understand the Dynasty

**Status:** ⬜ Not Started

**Goal:** Convert real CFB27 dynasty data into HuddleMind-owned data models.

### Python learning objectives

- ⬜ Dictionaries
- ⬜ JSON
- ⬜ Data validation
- ⬜ Type hints
- ⬜ Pydantic models
- ⬜ Parsing external data
- ⬜ Adapter pattern at a beginner-friendly level
- ⬜ Unit testing fundamentals

### Tasks

- ⬜ Evaluate current CFB27 parser options
- ⬜ Pick initial parser strategy
- ⬜ Parse program identity
- ⬜ Parse roster
- ⬜ Parse schedule
- ⬜ Parse game results
- ⬜ Parse injuries when available
- ⬜ Parse depth chart when available
- ⬜ Parse recruiting when available
- ⬜ Define HuddleMind player model
- ⬜ Define HuddleMind program model
- ⬜ Define HuddleMind season/week models
- ⬜ Define source-to-HuddleMind adapter
- ⬜ Validate data against the actual game UI
- ⬜ Add parser tests with sanitized fixtures

### Exit criteria

HuddleMind can read useful dynasty information and represent it using models that do not depend directly on the parser's internal schema.

---

## Milestone 4 — Local Memory

**Status:** ⬜ Not Started

**Goal:** Preserve HuddleMind history independently of the CFB27 save.

### Python learning objectives

- ⬜ Databases
- ⬜ SQL fundamentals
- ⬜ SQLite
- ⬜ Tables / rows / columns
- ⬜ Primary keys
- ⬜ Foreign keys
- ⬜ CRUD operations
- ⬜ Database migrations conceptually

### Tasks

- ⬜ Create local SQLite database
- ⬜ Store dynasty identity
- ⬜ Store sync snapshots / observations
- ⬜ Store players
- ⬜ Store schedule / results
- ⬜ Store recruiting observations
- ⬜ Store recommendation history
- ⬜ Preserve historical changes
- ⬜ Add database backup / reset development workflow

### Exit criteria

Restarting HuddleMind does not erase previously collected HuddleMind history.

---

## Milestone 5 — Cloud Bridge

**Status:** ⬜ Not Started

**Goal:** Synchronize normalized dynasty information to the web platform.

### Python learning objectives

- ⬜ Client/server architecture
- ⬜ HTTP
- ⬜ REST concepts
- ⬜ JSON requests
- ⬜ Authentication basics
- ⬜ Environment variables
- ⬜ API errors
- ⬜ Retries
- ⬜ Async concepts where useful

### Tasks

- ⬜ Create backend project
- ⬜ Configure development database
- ⬜ Create authentication model
- ⬜ Define bridge registration flow
- ⬜ Define dynasty synchronization API
- ⬜ Define normalized event schema
- ⬜ Send first event from Python bridge
- ⬜ Receive and store event in cloud
- ⬜ Add retry handling
- ⬜ Add local offline queue
- ⬜ Display bridge online/offline state
- ⬜ Secure credentials

### Exit criteria

A real update from the CFB27 PC appears in HuddleMind's cloud database without manually uploading a save through the website.

---

## Milestone 6 — Web Headquarters

**Status:** ⬜ Not Started

**Goal:** View the dynasty from a phone or another computer.

### Web learning / implementation topics

- ⬜ Next.js project setup
- ⬜ TypeScript basics as needed
- ⬜ Responsive layout
- ⬜ Authentication
- ⬜ Data fetching
- ⬜ Realtime updates

### Tasks

- ⬜ Create web application
- ⬜ Login
- ⬜ Dynasty selector
- ⬜ Program dashboard
- ⬜ Roster page
- ⬜ Schedule page
- ⬜ Recruiting page
- ⬜ Sync status
- ⬜ Mobile layout
- ⬜ Test from phone
- ⬜ Test from secondary PC

### Exit criteria

The user can open HuddleMind on a phone or second PC and see current synchronized dynasty information.

---

## Milestone 7 — Dynasty Brain

**Status:** ⬜ Not Started

**Goal:** Move from displaying data to generating useful recommendations.

### Python learning objectives

- ⬜ Derived values
- ⬜ Sorting / ranking
- ⬜ Rule engines
- ⬜ Scoring models
- ⬜ Basic statistics
- ⬜ Separating business rules from UI

### Tasks

- ⬜ Position-depth scoring
- ⬜ Future roster projection
- ⬜ Recruiting-need scoring
- ⬜ Recruiting movement alerts
- ⬜ Injury-impact alerts
- ⬜ Development alerts
- ⬜ Recommended action model
- ⬜ Recommendation explanations
- ⬜ Weekly staff report
- ⬜ Recommendation history
- ⬜ User feedback on recommendations

### Exit criteria

HuddleMind proactively identifies at least several useful dynasty actions and can explain the data behind them.

---

## Milestone 8 — Observe the Game

**Status:** ⬜ Not Started

**Goal:** Reliably understand the core live-game situation from the CFB27 window.

### Python learning objectives

- ⬜ Image arrays
- ⬜ Screen capture
- ⬜ OpenCV basics
- ⬜ Cropping / regions of interest
- ⬜ Template matching
- ⬜ OCR concepts
- ⬜ Confidence thresholds
- ⬜ State machines

### Tasks

- ⬜ Detect CFB27 window
- ⬜ Capture frames efficiently
- ⬜ Identify scoreboard region
- ⬜ Detect score
- ⬜ Detect quarter
- ⬜ Detect clock
- ⬜ Detect down
- ⬜ Detect distance
- ⬜ Detect field position
- ⬜ Detect possession
- ⬜ Add confidence values
- ⬜ Require multiple-frame confirmation
- ⬜ Stream game state to backend
- ⬜ Show live game page on phone

### Exit criteria

While playing, HuddleMind's second-screen dashboard updates the core game situation accurately enough for live recommendations.

---

## Milestone 9 — Offensive Coordinator v1

**Status:** ⬜ Not Started

**Goal:** Recommend useful offensive play calls in real time.

### Python learning objectives

- ⬜ Weighted scoring
- ⬜ Ranking algorithms
- ⬜ Feature engineering basics
- ⬜ Probability vs score
- ⬜ Historical aggregation
- ⬜ Performance measurement

### Tasks

- ⬜ Establish playbook data source
- ⬜ Normalize formations
- ⬜ Normalize plays
- ⬜ Tag concepts
- ⬜ Build candidate-play filter
- ⬜ Define situation-fit score
- ⬜ Define clock-strategy score
- ⬜ Define field-position score
- ⬜ Add user historical-success score
- ⬜ Add opponent tendency score
- ⬜ Add predictability penalty
- ⬜ Return top three plays
- ⬜ Add explanation factors
- ⬜ Show recommendations on live web page
- ⬜ Measure recommendation outcome

### Exit criteria

HuddleMind supplies three ranked play recommendations quickly enough to use during normal play calling and explains the main factors behind the ranking.

---

## Milestone 10 — Adaptive Coordinator

**Status:** ⬜ Not Started

**Goal:** Personalize recommendations using accumulated game history.

### Tasks

- ⬜ Track user formation tendencies
- ⬜ Track user concept tendencies
- ⬜ Track success by situation
- ⬜ Track opponent behavior during current game
- ⬜ Track opponent historical behavior when available
- ⬜ Adjust scores as the game evolves
- ⬜ Detect overused concepts
- ⬜ Detect tendency-breaking opportunities
- ⬜ Compare recommended vs actual results
- ⬜ Tune weights from real evidence

---

## Milestone 11 — Defensive Coordinator

**Status:** ⬜ Not Started

**Goal:** Recommend defensive responses using opponent tendencies and live situation.

### Tasks

- ⬜ Track opponent personnel
- ⬜ Track opponent formations
- ⬜ Track run/pass tendencies
- ⬜ Track target tendencies
- ⬜ Track QB scramble tendency
- ⬜ Define defensive-call representation
- ⬜ Build defensive scoring model
- ⬜ Recommend top defensive calls
- ⬜ Evaluate results

---

# 4. Learning Log

Use this section to record concepts after we actually use them.

## Python

| Lesson | Topic | Status | What I can now explain / do |
|---|---|---:|---|
| 01 | Paths and files | ⬜ | Not started |
| 02 | Loops, conditions, and functions | ⬜ | Not started |
| 03 | File watching and events | ⬜ | Not started |
| 04 | JSON and dictionaries | ⬜ | Not started |
| 05 | Type hints and Pydantic | ⬜ | Not started |
| 06 | SQLite and SQL | ⬜ | Not started |
| 07 | HTTP and APIs | ⬜ | Not started |
| 08 | Async / realtime concepts | ⬜ | Not started |
| 09 | Computer vision fundamentals | ⬜ | Not started |
| 10 | Statistics and scoring models | ⬜ | Not started |
| 11 | ML fundamentals, if justified | ⬜ | Not started |

### Lesson notes template

```text
## Lesson XX — Title

Date:
Feature:

What we built:

New Python concepts:

What I understand now:

What confused me:

Bugs we hit:

How we fixed them:

Code I want to revisit:

Next lesson:
```

---

# 5. Architecture Decisions

Record decisions here so we remember *why* something was chosen.

## ADR-001 — HuddleMind is web-first

**Status:** Accepted  
**Date:** 2026-09-16

### Decision

The primary HuddleMind interface will be a responsive web application accessible from a phone or another PC.

A lightweight Windows bridge will run on the PC hosting College Football 27.

### Why

- The user wants dynasty information on a phone / second screen.
- Only the gaming PC needs direct access to local CFB27 data.
- One web app avoids maintaining separate mobile and desktop UIs early in development.

---

## ADR-002 — Python powers the Windows bridge

**Status:** Accepted  
**Date:** 2026-09-16

### Decision

Python will be used for the local CFB27 bridge, data processing, computer vision, analytics, and recommendation logic where practical.

### Why

- Excellent file-system and data tooling.
- Strong computer-vision ecosystem.
- Good fit for analytics and future ML.
- The project doubles as a hands-on Python learning project.

---

## ADR-003 — Python is taught, not merely generated

**Status:** Accepted  
**Date:** 2026-09-16

### Decision

Instructional Python code will be developed incrementally by the user with guided explanations.

### Why

The explicit project goal includes improving the user's Python skills, not just producing HuddleMind as quickly as possible.

---

## ADR-004 — CFB27 integration starts read-only

**Status:** Accepted  
**Date:** 2026-09-16

### Decision

The first HuddleMind versions will observe saves and game visuals without modifying the CFB27 process or save files.

### Why

- Lower risk to dynasty saves.
- Less fragile across game patches.
- Easier to debug.
- Sufficient to prove the main product loop.

---

## ADR-005 — Normalize data before cloud sync

**Status:** Accepted  
**Date:** 2026-09-16

### Decision

The bridge will convert CFB27-specific data into HuddleMind-owned models/events before synchronization.

### Why

- Keeps the web app independent from CFB27 internals.
- Makes parser changes easier to isolate.
- Preserves the possibility of adapting HuddleMind to future CFB releases.
- Avoids making raw save files the cloud API contract.

---

## ADR-006 — Live play calls use a fast deterministic engine first

**Status:** Accepted  
**Date:** 2026-09-16

### Decision

Live play ranking will initially use explicit scoring/statistical logic. LLMs may explain recommendations but should not sit in the time-critical decision path.

### Why

- Predictable latency
- Easier debugging
- Easier evaluation
- Works offline more gracefully
- Recommendation factors remain understandable

---

# 6. Research / Unknowns Log

These are questions we need evidence for before locking architecture around them.

| Question | Status | Notes |
|---|---:|---|
| Exact current CFB27 dynasty save location and naming behavior | ⬜ | Verify on user's PC |
| Best current CFB27 parser foundation | ⬜ | Evaluate before Milestone 3 |
| Which dynasty tables/entities are reliably available | ⬜ | Validate against real save |
| Recruiting data completeness | ⬜ | Validate |
| Facilities / staff data availability | ⬜ | Validate |
| Reliable playbook extraction method | ⬜ | Needed before live coordinator |
| Whether selected plays can be detected visually | ⬜ | Prototype later |
| Most reliable scoreboard OCR/detection approach | ⬜ | Prototype in Milestone 8 |
| Whether game UI scale changes affect recognition | ⬜ | Test multiple resolutions |
| Supabase vs alternate backend after prototype | ⬜ | Keep architecture portable |

---

# 7. Blockers

No active blockers.

When a blocker appears, record:

```text
### Blocker — Short title

Status:
Date found:
Milestone:

Problem:

What we tried:

Evidence:

Next experiment:

Resolution:
```

---

# 8. Bugs / Technical Debt

None recorded yet.

Use:

```text
### BUG-001 — Short title

Status:
Severity:
Found in:

Expected:

Actual:

Steps to reproduce:

Cause:

Fix:
```

---

# 9. Product Backlog

Ideas that are valuable but should not distract from the current milestone.

- ⬜ PWA install experience
- ⬜ Push notifications for important dynasty alerts
- ⬜ Voice coordinator mode
- ⬜ Apple Watch / wearable glance view
- ⬜ Compare seasons
- ⬜ Compare multiple dynasties
- ⬜ Recruiting class grading
- ⬜ Scheme-fit ratings
- ⬜ Player-development projections
- ⬜ Transfer / departure risk modeling if data allows
- ⬜ Automated opponent scouting report
- ⬜ Drive-by-drive game summary
- ⬜ Halftime AI adjustments report
- ⬜ Postgame coordinator grade
- ⬜ Fourth-down decision model
- ⬜ Clock-management assistant
- ⬜ Two-minute drill mode
- ⬜ Red-zone specialist recommendations
- ⬜ Tendency heatmaps
- ⬜ Historical coaching profile
- ⬜ Ask HuddleMind conversational assistant
- ⬜ Local-model support
- ⬜ Export season report

---

# 10. Change Log

## 2026-09-16

### Added

- Selected **HuddleMind** as the project name.
- Defined web-first architecture.
- Defined Windows Python bridge concept.
- Added product PRD.
- Added project / learning progress tracker.
- Established Python learning-first development rule.
- Established read-only-first CFB27 integration strategy.
- Established fast-brain / deep-brain recommendation split.

---

# 11. Next Session

## Lesson 1 — Find the Dynasty

### Objective

Write the first HuddleMind Python code ourselves and use it to locate the College Football 27 save directory.

### We will learn

- What `import` means
- Variables
- Strings
- `pathlib`
- `Path.home()`
- Joining paths
- Checking whether a directory exists
- Printing useful debugging information

### Target result

A tiny Python program that can answer:

> Where does HuddleMind expect CFB27 saves to live, and does that directory exist on this PC?

We will build from there instead of jumping directly to a completed save watcher.
