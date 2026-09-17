# HuddleMind — Project Progress & Learning Tracker

**Repository:** `bworthy89/HuddleMind`  
**Current Phase:** Milestone 0 — Foundation  
**Current Status:** 🟡 In Progress  
**Last Updated:** 2026-09-16

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
- ✅ Python target selected: **3.12**
- ✅ Dependency approach selected: built-in `venv` + `pip`
- ✅ Development setup documented
- ✅ Initial web-app folder strategy documented
- ✅ Architecture diagram and data flow documented
- ✅ First development workflow documented
- ✅ Bridge learning-first rules documented

### Still to do on the development PC

- ⬜ Clone/pull the current repository
- ⬜ Confirm Python 3.12 is installed
- ⬜ Create `.venv`
- ⬜ Activate `.venv`
- ⬜ Verify `python --version`
- ⬜ Confirm Git is working from the repo

### Exit criteria

Milestone 0 is complete when the development PC can clone the repository, activate a Python 3.12 virtual environment, and is ready to run the first bridge script.

### Immediate next step

**Lesson 1 — Find the Dynasty**

We will create the first Python file together. The project owner will type the instructional Python code while each concept is explained and tested.

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
| 0 | Foundation | 🟡 |
| 1 | Find the Dynasty | ⬜ |
| 2 | Watch the Dynasty | ⬜ |
| 3 | Understand the Dynasty | ⬜ |
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

**Status:** ⬜ Not Started

**Goal:** Use Python to reliably locate CFB27 dynasty save files without modifying them.

### Python learning objectives

- ⬜ What a Python script is
- ⬜ `import`
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

- ⬜ Create the first bridge Python file
- ⬜ Print the Windows user's home directory
- ⬜ Build candidate paths
- ⬜ Verify the actual CFB27 folder layout
- ⬜ Locate the save directory
- ⬜ List files inside it
- ⬜ Identify likely dynasty files
- ⬜ Print file names and modification times
- ⬜ Refactor discovery into a reusable function
- ⬜ Add useful missing-folder errors
- ⬜ Test with a real CFB27 dynasty
- ⬜ Document the verified save layout

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

- Add `watchdog`
- Watch the verified save directory
- Filter unrelated events
- Debounce duplicate events
- Log meaningful dynasty changes
- Test by advancing a real dynasty

---

## Milestone 3 — Understand the Dynasty

**Goal:** Convert CFB27 data into HuddleMind-owned models.

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
| 01 | Paths and files | ⬜ | Not started |
| 02 | Conditions, loops, and functions | ⬜ | Not started |
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

Use Python 3.12, built-in `venv`, and `pip` initially. Add more advanced dependency tooling only when it solves a real problem.

---

# 7. Research / Unknowns

| Question | Status | Notes |
|---|---:|---|
| Exact CFB27 dynasty save location/naming on this PC | ⬜ | Verify in Lesson 1 |
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

**Local setup pending:** the Python 3.12 virtual environment still needs to be created and verified on the development PC.

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

# 11. Next Session — Lesson 1

## Find the Dynasty

### Before writing Python

On the Windows development PC:

1. Clone/pull `bworthy89/HuddleMind`.
2. Open a terminal in the repo.
3. Confirm Python 3.12.
4. Create `.venv`.
5. Activate `.venv`.

### Then we write the first Python ourselves

We will start with only enough code to answer:

> What is this Windows user's home directory?

Then we will build from that result toward discovering the actual CFB27 save location.

### First concepts

- `import`
- Variables
- `pathlib`
- `Path.home()`
- Objects
- Methods
- Printing/debugging values

We will not jump directly to a completed save watcher.
