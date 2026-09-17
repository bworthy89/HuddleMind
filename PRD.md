# HuddleMind — Product Requirements Document

**Status:** Draft v0.1  
**Product:** HuddleMind  
**Platform:** College Football 27 on PC + Web App  
**Primary User:** Solo dynasty player / coach  
**Repository:** `bworthy89/HuddleMind`

---

## 1. Product Summary

HuddleMind is an AI-powered companion platform for College Football 27 on PC. It runs a lightweight Windows bridge beside the game, observes dynasty and live-game information, converts that information into structured HuddleMind data, and synchronizes it to a responsive web application that can be viewed from a phone, tablet, laptop, or another PC.

HuddleMind has two core jobs:

1. **Dynasty Intelligence** — continuously analyze the user's program and proactively recommend recruiting, roster, depth-chart, staff, facilities, scheduling, development, and other dynasty actions.
2. **Live Coordinator** — analyze the current game situation and recommend offensive and eventually defensive play calls based on down, distance, score, clock, field position, personnel, the user's tendencies, opponent tendencies, and historical results.

The long-term goal is for HuddleMind to feel less like a static stats dashboard and more like a persistent coaching staff that learns the user's program, scheme, tendencies, and decision history over multiple seasons.

---

## 2. Product Vision

> Turn a College Football 27 dynasty into a living data-driven coaching environment where an AI staff continuously watches, learns, and helps the user make better program and in-game decisions.

HuddleMind should eventually behave like a combination of:

- Head coach assistant
- Recruiting coordinator
- Roster / personnel analyst
- Offensive coordinator
- Defensive coordinator
- Opponent scout
- Program analytics department
- Historical coaching journal

The user should not have to manually re-enter information that HuddleMind can reliably observe or derive from College Football 27.

---

## 3. Product Principles

### 3.1 Read-first integration

The first versions of HuddleMind should observe College Football 27 rather than modify or control it.

Prefer, in order:

1. Reading supported local dynasty/save information.
2. Observing the game window.
3. Deriving structured state from screenshots / computer vision.
4. Maintaining HuddleMind's own historical database.

Direct game-process injection or memory modification is **not** required for the MVP and should not be introduced without a clear need, technical review, and safety assessment.

### 3.2 Web-first experience

The main user interface is a responsive web application.

The Windows bridge exists to connect the local PC game to HuddleMind. It should not become the primary UI.

The web application should work well on:

- iPhone
- Android phones
- Tablets
- Desktop browsers
- Laptops
- Secondary PCs

A Progressive Web App (PWA) experience is preferred once the core dashboard is stable.

### 3.3 Fast brain + deep brain

Live play calling must not depend entirely on a slow LLM request.

HuddleMind should separate intelligence into:

**Fast brain**
- Situation scoring
- Play ranking
- Clock logic
- Down / distance logic
- Historical success rates
- Opponent tendency matching
- User tendency analysis

**Deep brain**
- Weekly dynasty summaries
- Recruiting strategy
- Roster planning
- Opponent scouting reports
- Natural-language explanations
- Long-term pattern recognition

### 3.4 Explain recommendations

Recommendations should explain **why** they were made whenever possible.

Bad:

> Run Mesh.

Better:

> Mesh is the top recommendation on 3rd & 5 because the opponent has blitzed on 5 of its last 7 third downs, and your offense has converted 71% of similar situations with Mesh this season.

### 3.5 Learn the user

HuddleMind should become personalized over time.

It should learn:

- Frequently used formations
- Favorite concepts
- Success by play
- Success by down / distance
- Run / pass tendencies
- Red-zone tendencies
- Fourth-down behavior
- Recruiting habits
- Position-group preferences
- Roster construction patterns
- Historical strengths and weaknesses

---

## 4. Learning Requirement — Python

HuddleMind is also a hands-on Python learning project for the owner.

For all Python portions of the project, development should be taught step by step rather than delivered primarily as completed implementations.

### Teaching workflow

For each Python feature:

1. Explain what is being built.
2. Explain why HuddleMind needs it.
3. Introduce the Python concepts involved.
4. Have the user write a small working piece.
5. Run and inspect the result.
6. Debug together.
7. Add the next piece incrementally.
8. Refactor only after the behavior is understood.
9. Update project documentation and the learning log.

Large completed Python implementations should only be supplied when the user explicitly asks for them or when the code is non-instructional boilerplate.

The goal is not only to finish HuddleMind. The goal is for the user to understand and be able to explain the Python code that powers it.

---

## 5. Target User

### Primary persona — Dynasty Coach

A College Football 27 PC player who:

- Plays long-running Dynasty saves.
- Wants better recruiting and roster decisions.
- Wants deeper analytics than the base game exposes.
- Wants an assistant that remembers historical program information.
- Wants in-game play suggestions based on actual game context.
- May use a phone or second screen while playing.

### Secondary future persona — Advanced Dynasty Player

A user who wants detailed historical analysis, program comparisons, scheme analytics, and coaching tendencies across multiple dynasties.

Multi-user support is not required for the first MVP.

---

## 6. Core Product Components

### 6.1 HuddleMind Bridge

A lightweight Windows application/service running on the PC where College Football 27 is installed.

Responsibilities:

- Locate supported CFB27 dynasty data.
- Detect when dynasty data changes.
- Parse or consume parsed dynasty information.
- Normalize CFB27 data into HuddleMind models.
- Maintain a local cache.
- Observe the CFB27 game window during live games.
- Derive live game state.
- Run low-latency local recommendation logic when needed.
- Synchronize events with the HuddleMind backend.
- Recover gracefully when the internet connection is unavailable.

The bridge should contain as little UI as reasonably necessary.

### 6.2 HuddleMind Web App

The primary interface.

Responsibilities:

- Authentication
- Dynasty selection
- Program dashboard
- AI staff report
- Recruiting analysis
- Roster analysis
- Depth chart
- Schedule / results
- Player development
- Opponent scouting
- Live game dashboard
- Play-call recommendations
- Analytics
- Recommendation history
- Settings

### 6.3 HuddleMind Backend

Responsibilities:

- User identity
- Dynasty ownership
- Cloud persistence
- Realtime event delivery
- Historical data
- Recommendation storage
- AI orchestration
- API access for bridge and web app

### 6.4 Recommendation Engine

A deterministic/statistical engine that scores possible actions and plays.

It should support explicit factors and tunable weights before machine learning is introduced.

### 6.5 AI Reasoning Layer

Used for:

- Explaining recommendations
- Weekly staff reports
- Recruiting summaries
- Roster planning
- Opponent scouting summaries
- Conversational questions about the user's dynasty

The LLM is an explanation / reasoning layer, not the sole source of truth for live play selection.

---

## 7. Major Features

## 7.1 Dynasty Detection

HuddleMind should detect available supported dynasty saves and identify the currently active dynasty where possible.

### Requirements

- Detect the expected CFB27 save location.
- Enumerate candidate dynasty saves.
- Track file modification timestamps.
- Detect meaningful save changes.
- Associate a local save with a HuddleMind dynasty ID.
- Never overwrite the original save during normal read-only operation.

### MVP acceptance criteria

- User starts the bridge.
- Bridge can identify at least one supported dynasty save.
- Bridge reports the detected dynasty to the application.
- A save modification produces a new synchronization event.

---

## 7.2 Dynasty Import / Synchronization

The bridge should translate game-specific data into HuddleMind's internal data model.

Initial target entities:

- Program
- Season
- Week
- Players
- Positions
- Player ratings / attributes when available
- Depth chart
- Injuries
- Schedule
- Results
- Game statistics
- Recruiting targets
- Recruiting status
- Coaches / staff when available
- Program attributes / facilities when available

### Requirements

- Store source IDs when available.
- Track when data was last observed.
- Prefer incremental updates over complete cloud reuploads.
- Preserve history rather than replacing all historical state.

---

## 7.3 Program Dashboard

The dashboard is the landing page for the selected dynasty.

### Display

- Team
- Current season / week
- Record
- Ranking when available
- Next opponent
- Recent results
- Program alerts
- Recruiting alerts
- Roster alerts
- Injury alerts
- Top AI recommendations
- Current HuddleMind sync status

### Goal

A user should understand the most important things happening in the program within approximately 30 seconds.

---

## 7.4 AI Staff Report

Generate a report after meaningful dynasty updates, especially after advancing a week.

Possible sections:

- Week overview
- Program health
- Recruiting priorities
- Roster risks
- Injury impact
- Development opportunities
- Upcoming opponent
- Recommended actions

Every recommended action should link to the supporting HuddleMind data when possible.

---

## 7.5 Recruiting Intelligence

HuddleMind should help the user allocate attention based on team needs and recruiting movement.

### Initial recommendations

- Position priority
- Prospect priority
- Recruiting momentum changes
- Roster-need warnings
- Over-recruiting warnings
- Under-recruiting warnings
- Potential fallback targets

### Later intelligence

- Expected future depth
- Class balance
- Historical development results
- Scheme fit
- Replacement urgency

---

## 7.6 Roster Intelligence

Analyze the roster by current and future depth.

### Capabilities

- Position-group depth
- Graduation / departure risk
- Development opportunities
- Depth-chart suggestions
- Redshirt candidates
- Weak position groups
- Recruiting needs derived from projected roster
- Historical player development

---

## 7.7 Opponent Scouting

Before each game, create a scouting report using available dynasty/game information.

Possible sections:

- Opponent record
- Team strengths / weaknesses
- Key players
- Recent performance
- Offensive tendencies
- Defensive tendencies
- Suggested offensive approach
- Suggested defensive approach
- Matchups to target

---

## 7.8 Live Game Observer

During a game, the bridge observes the CFB27 window.

### MVP state fields

- User possession
- Score
- Opponent score
- Quarter
- Game clock
- Down
- Distance
- Field position

### Later fields

- Formation
- Personnel
- Selected play
- Opponent defensive shell
- Box count
- Coverage clues
- Motion
- Result of previous play

### Requirements

- Observation must not require manually typing every game state.
- Confidence should be tracked for computer-vision-derived fields.
- HuddleMind should avoid making high-confidence claims from low-confidence observations.

---

## 7.9 Live Offensive Coordinator

Recommend ranked offensive plays during the game.

### Inputs

- Down
- Distance
- Field position
- Score differential
- Quarter
- Clock
- Timeouts when available
- Current playbook
- Personnel
- User play history
- User success history
- Opponent tendencies
- Recent play sequence

### Output

At least:

1. Top recommended play
2. Two alternatives
3. Recommendation score or confidence
4. Short explanation
5. Relevant tendency warning

### Example

> **1. Gun Trips — Inside Zone**  
> Opponent has shown a light box on 5 of the last 7 snaps from this personnel. You are averaging 5.8 yards per attempt on Inside Zone this season.

---

## 7.10 Live Defensive Coordinator

Not required for the first live-play MVP.

Later capabilities:

- Offensive personnel recognition
- Run/pass tendency
- Formation tendency
- Target distribution
- QB scramble behavior
- Coverage recommendations
- Pressure recommendations
- Spy recommendations
- Red-zone recommendations

---

## 7.11 Playbook Database

HuddleMind should maintain a structured representation of plays that are actually relevant to the user's playbook.

Potential fields:

- Play ID
- Playbook
- Formation
- Personnel
- Concept
- Run / pass
- Direction
- Routes
- Blocking family
- Play action
- RPO
- Situational tags

The live coordinator should eventually recommend only plays the user can actually call.

---

## 7.12 Play History and Tendencies

Every observed play should eventually create a historical record.

Potential fields:

- Game
- Opponent
- Quarter
- Clock
- Down
- Distance
- Field position
- Formation
- Play
- Defensive look
- Result
- Yards
- Success / failure
- Turnover
- Score differential

Derived analytics:

- Success by play
- Success by concept
- Success by formation
- Success by situation
- Run/pass tendency
- Formation tendency
- Red-zone tendency
- Third-down tendency
- Fourth-down tendency

---

## 7.13 Multi-Dynasty Support

The data model should support multiple dynasties even if the first development cycle focuses on one.

Each dynasty should maintain independent:

- Program history
- Players
- Seasons
- Recruiting history
- Games
- Tendencies
- Recommendations

---

## 7.14 Ask HuddleMind

Future conversational interface grounded in the user's HuddleMind data.

Example questions:

- Why is offensive tackle my biggest recruiting need?
- Who should I redshirt?
- What formations have worked best on third down?
- Which recruits can I afford to stop pursuing?
- What changed after last week's game?
- How has this team compared with my 2028 team?

Answers must be grounded in stored dynasty information rather than invented statistics.

---

## 8. Live Play Recommendation Model

The first recommendation model should be understandable and tunable.

Example conceptual scoring function:

```text
play_score =
    situation_fit
  + personnel_matchup
  + opponent_tendency
  + historical_user_success
  + field_position_fit
  + clock_strategy
  + tendency_break_value
  - turnover_risk
  - predictability_penalty
```

Initial weights should be hand-tuned and documented.

Machine learning should be considered only after enough real play-history data exists to evaluate whether it improves recommendations.

---

## 9. Event Model

The bridge should send normalized HuddleMind events rather than treating raw save files as the cloud API contract.

Example event types:

```text
bridge_online
bridge_offline
dynasty_detected
dynasty_updated
week_advanced
roster_updated
recruiting_updated
injury_updated
game_started
game_state_updated
play_observed
play_completed
game_completed
```

Example conceptual game-state event:

```json
{
  "event": "game_state_updated",
  "dynasty_id": "...",
  "quarter": 3,
  "clock": "05:18",
  "down": 2,
  "distance": 6,
  "yard_line": 43,
  "score_for": 24,
  "score_against": 21
}
```

The exact schema will be defined during implementation.

---

## 10. Proposed Technical Architecture

```text
College Football 27
        |
        v
HuddleMind Windows Bridge
(Python)
        |
        | HTTPS / realtime events
        v
HuddleMind Backend / API
        |
        +------ PostgreSQL
        |
        +------ AI services
        |
        +------ Realtime channel
        |
        v
HuddleMind Web App
(Phone / tablet / browser / second PC)
```

### Proposed stack

#### Windows bridge
- Python 3.12+
- `pathlib`
- `watchdog`
- Pydantic
- SQLite
- FastAPI where a local API is useful
- OpenCV for computer vision
- DXCam or equivalent capture library when needed

#### Web
- Next.js
- TypeScript
- Tailwind CSS
- Responsive / mobile-first UI
- PWA later

#### Backend
- PostgreSQL
- Supabase as the initial managed backend candidate
- Realtime events
- Authentication

#### AI
- OpenAI API initially
- Deterministic/statistical recommendation engine for low-latency decisions
- Optional local models later if justified

The stack is a starting point and may change as the project learns more about CFB27's available data.

---

## 11. Data Ownership and Privacy

HuddleMind should minimize unnecessary data collection.

Principles:

- Original CFB27 saves remain local by default.
- Send normalized HuddleMind data rather than uploading entire save files unless a future feature explicitly requires otherwise.
- Authenticate bridge-to-cloud communication.
- Use per-user dynasty ownership controls.
- Store secrets outside source control.
- Never commit API keys or service-role credentials.
- Allow local caching when cloud access is unavailable.

---

## 12. Reliability Requirements

The bridge must fail safely.

If HuddleMind cannot parse or observe something:

- Do not modify the user's CFB27 save.
- Log the error.
- Report sync health.
- Preserve previously valid HuddleMind state.
- Retry recoverable network operations.

The live coordinator should continue basic local recommendations where possible during internet outages.

---

## 13. Performance Targets

These are initial product targets, not guarantees.

### Dynasty sync

- Detect a meaningful save change within a few seconds.
- Update the web dashboard soon after normalized data is available.

### Live coordinator

- Game-state detection should feel near-real-time.
- Deterministic play ranking should target sub-second execution.
- LLM-generated explanations must not block the underlying recommendation.

---

## 14. MVP Scope — v0.1

The first complete milestone proves the end-to-end bridge.

### v0.1 goal

> Start CFB27, load a dynasty, let the Windows bridge detect and parse useful dynasty information, synchronize it to HuddleMind, and view that information from a phone or another computer.

### Included

- Python development environment
- HuddleMind Bridge project skeleton
- Save-path discovery
- Dynasty save detection
- File-change detection
- Initial normalized data models
- Initial parser integration / adapter
- Local SQLite cache
- Cloud authentication
- Dynasty synchronization
- Basic web dashboard
- Program overview
- Roster view
- Schedule view
- Recruiting view if parser data is sufficiently reliable
- Sync-status indicator

### Not included

- Live play calling
- Defensive coordinator
- Full computer vision
- Machine learning
- Automated game control
- Save editing

---

## 15. Planned Milestones

### Milestone 0 — Foundation

- Repository established
- PRD
- Progress tracker
- Python environment
- Project structure
- Development documentation
- Secret-management rules

### Milestone 1 — Find the Dynasty

- Learn `pathlib`
- Locate CFB27 save directory
- List dynasty candidates
- Identify selected save
- Detect modification timestamps

### Milestone 2 — Watch the Dynasty

- Learn functions, classes, events, and packages
- Add file-system watcher
- Detect save changes
- Create bridge logging
- Create basic bridge status

### Milestone 3 — Understand the Dynasty

- Integrate or adapt a supported CFB27 parser
- Convert parser output to HuddleMind models
- Validate roster / schedule / recruiting data
- Persist normalized snapshots locally

### Milestone 4 — Cloud Bridge

- Define API/event schema
- Authenticate the bridge
- Create remote dynasty
- Synchronize normalized state
- Handle retry / offline queue

### Milestone 5 — Web Headquarters

- Create responsive web app
- Dynasty selector
- Dashboard
- Roster
- Schedule
- Recruiting
- Sync health

### Milestone 6 — Dynasty Brain

- Build rule-based alerts
- Position-depth analysis
- Recruiting priority analysis
- Weekly staff report
- Recommendation history

### Milestone 7 — Observe the Game

- Capture CFB27 window
- Identify scoreboard regions
- Detect score
- Detect quarter / clock
- Detect down / distance
- Detect field position
- Stream game state to web app

### Milestone 8 — Offensive Coordinator v1

- Build play database
- Track plays / outcomes
- Define play-scoring model
- Rank candidate plays
- Display top three recommendations
- Explain recommendation factors

### Milestone 9 — Adaptive Coordinator

- User tendency model
- Opponent tendency model
- Historical success model
- Situation-specific recommendations
- Recommendation-result evaluation

### Milestone 10 — Defensive Coordinator

- Recognize offensive situations
- Track opponent offensive tendencies
- Recommend defensive calls

---

## 16. Non-Goals for Early Development

HuddleMind is not initially intended to:

- Automatically play the game.
- Send controller inputs.
- Alter online competition.
- Inject code into the game process.
- Edit dynasty saves during normal operation.
- Guarantee optimal football strategy.
- Replace user decision-making.
- Train an ML model before sufficient data exists.

---

## 17. Risks and Unknowns

### CFB27 data stability

Game patches may alter save structures or UI locations.

**Mitigation:** Isolate CFB-specific parsing and observation behind adapters so the rest of HuddleMind remains stable.

### Live-state recognition

Computer vision may misread small or animated UI elements.

**Mitigation:** Confidence scoring, multiple-frame confirmation, narrow capture regions, and manual debugging tools.

### Play recognition

Reliably recognizing the selected play and defensive look may be significantly harder than scoreboard state.

**Mitigation:** Build live coordination in layers rather than making pre-snap recognition a v1 dependency.

### Latency

Cloud round trips and LLM requests are inappropriate for time-critical decisions.

**Mitigation:** Keep the first-stage recommendation engine local and deterministic.

### Parser dependency

Community parser behavior may change.

**Mitigation:** Use an adapter interface and maintain HuddleMind's own normalized data model.

---

## 18. Success Metrics

Early success is functional rather than commercial.

### v0.1

- User can detect a real CFB27 dynasty.
- User can see synchronized dynasty information on another device.
- Sync happens without manual re-entry.
- Original save remains untouched.

### Dynasty Brain

- Recommendations reference real HuddleMind data.
- User can see why an action was suggested.
- Recommendations are stored and reviewable.

### Live Coordinator

- HuddleMind reliably recognizes core game state.
- Play recommendations arrive before the user needs to select a play.
- The user can inspect the factors behind a recommendation.
- HuddleMind can evaluate recommendation results over time.

### Learning goal

- The user can explain the major Python modules they built.
- The learning log shows progression from basic file handling through APIs, realtime communication, computer vision, and analytics.

---

## 19. Open Product Questions

These should be answered through development rather than guessed too early.

- Which CFB27 save/parser source will be the most reliable foundation?
- Which exact dynasty entities can be read consistently?
- What game-state fields can be recognized reliably from the UI?
- Can selected plays be observed reliably without invasive game integration?
- How should playbook assets be normalized?
- Which recommendation factors prove most predictive?
- How often should historical snapshots be stored?
- Which features truly need an LLM versus deterministic logic?
- What information should remain local versus cloud-synchronized?

---

## 20. Definition of Done for the First End-to-End Prototype

The first prototype is complete when:

1. The user launches HuddleMind Bridge on the CFB27 PC.
2. The bridge identifies a supported dynasty.
3. The bridge reads at least basic program, roster, and schedule information.
4. The bridge converts the information to HuddleMind's normalized models.
5. The information is persisted locally.
6. The bridge securely synchronizes it to the backend.
7. The user opens the HuddleMind website from a second device.
8. The correct dynasty information appears without manually importing a file through the web UI.
9. A subsequent dynasty update is detected and synchronized.
10. The workflow is documented well enough to reproduce from a clean development environment.

---

## 21. Documentation Rule

Documentation is part of the feature, not a cleanup task after the feature.

Every meaningful milestone should update the appropriate documentation with:

- What was built
- Why it was built
- Architecture decisions
- Setup changes
- Data-model changes
- Python concepts learned
- Known limitations
- Next steps

See `PROJECT_PROGRESS.md` for the living project and learning tracker.
