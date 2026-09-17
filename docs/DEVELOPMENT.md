# HuddleMind Development Guide

**Last Updated:** 2026-09-16

This guide defines the initial local-development workflow for HuddleMind.

HuddleMind is intentionally being built in small stages so the project owner can learn the Python powering the bridge instead of receiving a finished implementation all at once.

## 1. Prerequisites

For the first bridge milestone, install:

- Git
- Python **3.12**
- A code editor (VS Code is a good default)

Node.js is not required until web development begins.

## 2. Clone the Repository

From a Windows terminal:

```powershell
git clone https://github.com/bworthy89/HuddleMind.git
cd HuddleMind
```

## 3. Python Environment Strategy

We are starting with Python's built-in virtual environments and `pip`.

Why:

- It exposes the fundamentals clearly.
- It avoids hiding environment behavior behind additional tooling too early.
- It is enough for the first bridge milestones.

We may adopt another package/dependency tool later if the project develops a real need for it.

### Create the bridge virtual environment

Run this from the repository root:

```powershell
python -m venv .venv
```

Activate it in PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Confirm which Python is active:

```powershell
python --version
```

Expected major/minor version:

```text
Python 3.12.x
```

### If PowerShell blocks activation

Do not change system policy blindly. We will diagnose the exact message together first.

## 4. Dependency Strategy

Do not install libraries simply because we may use them eventually.

Add a dependency when the current feature needs it.

Early progression:

1. Standard library only for Lesson 1.
2. `watchdog` when we begin filesystem event watching.
3. Data-validation/database/CV libraries only when their milestones begin.

This keeps the learning surface small and makes it obvious why each dependency exists.

## 5. Initial Repository Areas

### `bridge/`

Windows-side CFB27 integration, Python data processing, live observation, and low-latency recommendation logic.

### `web/`

Responsive HuddleMind browser experience. It is a placeholder until the bridge proves it can reliably produce useful normalized data.

### `docs/`

Architecture, setup, decisions, and future technical documentation.

## 6. Secrets and Environment Variables

Never commit:

- API keys
- Database passwords
- Supabase service keys
- Authentication secrets
- Personal tokens
- Private URLs containing credentials

Local secrets will live in `.env` files when needed. `.env` files are ignored by Git.

When the project first needs environment variables, add a safe `.env.example` containing variable names and non-secret placeholders.

Example pattern for later use:

```text
SERVICE_URL=
SERVICE_PUBLIC_KEY=
```

Do not place real values in `.env.example`.

## 7. Local Game Data Rules

Do not commit:

- Raw CFB27 save files
- User-specific local databases
- Screen captures containing personal information
- Debug dumps generated from private saves

If we need test data in the repository, create a deliberately sanitized fixture containing only the minimum data required for the test.

## 8. Python Learning Workflow

For instructional Python features, use this cycle:

```text
Understand the feature
        ↓
Learn one concept
        ↓
Write a small piece
        ↓
Run it
        ↓
Explain the output
        ↓
Debug if needed
        ↓
Add the next concept
        ↓
Document what was learned
```

Do not jump directly to a finished large module unless explicitly requested.

## 9. First Development Workflow

### Lesson 1 — Find the Dynasty

The first coding session should use only Python's standard library.

Sequence:

1. Create and activate `.venv`.
2. Create the first bridge Python file during the lesson.
3. Import `Path` from `pathlib`.
4. Discover the current Windows user's home directory.
5. Build paths from that location.
6. Check whether candidate directories exist.
7. Inspect the actual CFB27 folder layout on the user's machine.
8. List candidate save files.
9. Refactor repeated logic into a small function only after the basics are understood.

The exact CFB27 save path is **not hardcoded into the architecture documentation yet**. We will verify it against the user's real PC first.

## 10. Git Workflow

Keep commits small and descriptive.

Examples:

```text
docs: add bridge setup notes
feat(bridge): locate user home directory
feat(bridge): list dynasty save candidates
fix(bridge): handle missing save directory
```

For learning sessions, it is useful to commit after a small working milestone rather than after every line.

## 11. Definition of Done for a Learning Feature

A Python learning feature is complete when:

- The behavior works on the user's machine.
- The user can explain the main concepts introduced.
- Important errors have understandable messages.
- Relevant tests are added when the project reaches the testing stage.
- `PROJECT_PROGRESS.md` is updated.
- Important architectural discoveries are documented.

## 12. Before Adding New Technology

Ask:

1. What problem are we solving right now?
2. Can the standard library/current stack solve it clearly?
3. What will the new dependency teach or simplify?
4. Does it create unnecessary complexity?

HuddleMind should grow because requirements demand it, not because a technology is fashionable.
