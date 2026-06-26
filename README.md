# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## ✨ Features

- **Priority-aware daily planning** — `Scheduler.build_plan()` fits tasks into the owner's available minutes, placing fixed-time tasks first and greedily filling the rest by priority (high first), so the most important care happens even when time is tight.
- **Sorting by time** — `Scheduler.sort_by_time()` returns tasks in chronological order (by `fixed_time`), with flexible/no-time tasks last; the generated plan is kept time-ordered.
- **Priority + duration sorting** — `Scheduler.sort_tasks()` ranks by priority, breaking ties by shortest duration to squeeze more tasks into leftover time.
- **Filtering by pet & status** — `Pet.pending_tasks()` and `Owner.filter_tasks(pet_name=, completed=)` let you view tasks for one pet and/or hide completed ones; completed tasks are automatically excluded from new plans.
- **Conflict warnings** — `ScheduledTask.overlaps()` + `Scheduler.find_conflicts()` flag overlapping time slots (same pet *or* across pets) and return warning strings instead of crashing.
- **Daily / weekly recurrence** — completing a recurring task (`Pet.complete_task()` → `CareTask.next_occurrence()`) auto-creates the next instance using `timedelta` (+1 day or +7 days); one-off tasks don't repeat.
- **Plain-language explanations** — every plan includes a `summary()` and an `explanation` describing what was scheduled, what was skipped, and why.

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Terminal output from running `python main.py`:

```
Today's Schedule for Jordan (90 min available per pet)
============================================================

Mochi (dog):
  07:00-07:30  Morning walk (30 min) [priority: high]
  07:30-07:55  Enrichment play (25 min) [priority: medium]
  08:00-08:05  Give meds (5 min) [priority: high]
  Skipped (out of time):
    - Grooming (40 min)
  Total: 60 min planned
  Why: Placed 3 task(s) using 60 of 90 available minutes. Skipped 1 task(s) once time ran out, keeping higher-priority tasks first.

Biscuit (cat):
  07:00-07:10  Litter cleanup (10 min) [priority: medium]
  07:10-07:25  Laser play (15 min) [priority: low]
  07:30-07:40  Feed breakfast (10 min) [priority: high]
  Total: 35 min planned
  Why: Placed 3 task(s) using 35 of 90 available minutes.
```

## 🧪 Testing PawPal+

Run the full test suite from the project root:

```bash
python -m pytest
```

**What the tests cover** (`tests/test_pawpal.py`, 26 tests):

- **Model basics** — adding/removing tasks, registering pets, marking tasks complete.
- **Scheduling** — priority + shortest-first sort order, the time-budget `fits()` check, skipping tasks when time runs out, and placing `fixed_time` tasks at their slot.
- **Sorting** — `sort_by_time()` returns tasks in chronological order with flexible (no-time) tasks last.
- **Filtering** — `pending_tasks()` and `Owner.filter_tasks()` by pet name and/or completion status.
- **Recurrence** — completing a daily task regenerates it for the next day, weekly for +7 days, and one-off tasks do not regenerate.
- **Conflict detection** — overlapping time slots are flagged (same pet and across pets), while spaced/touching tasks are not.

Successful test run:

```
============================= test session starts =============================
platform win32 -- Python 3.14.5, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\skkpr\Desktop\Github - codepath\ai110-module2show-pawpal-starter
plugins: anyio-4.14.1
collected 26 items

tests\test_pawpal.py ..........................                          [100%]

============================= 26 passed in 0.23s ==============================
```

### Confidence Level

**★★★★☆ (4/5)** — The core scheduling, sorting, filtering, recurrence, and conflict-detection paths are all tested with both positive and negative cases, and all 26 tests pass. Holding back one star because conflict detection currently only *reports* overlaps (the scheduler doesn't yet resolve them), and recurrence covers daily/weekly but not month-end or custom intervals. Those are the next areas I'd test and harden.

## 📐 Smarter Scheduling

Beyond a basic to-do list, PawPal+ adds four scheduling behaviors. All logic
lives in `pawpal_system.py` and is covered by `tests/test_pawpal.py`.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_tasks()`, `Scheduler.sort_by_time()` | `sort_tasks` orders by priority (high first), then shortest duration to fit more tasks; `sort_by_time` orders chronologically by `fixed_time`, with flexible (no-time) tasks last. |
| Filtering | `Pet.pending_tasks()`, `Owner.filter_tasks(pet_name=, completed=)` | Filter out completed tasks, or list tasks by pet name and/or completion status. |
| Conflict handling | `ScheduledTask.overlaps()`, `Scheduler.find_conflicts()` | Half-open `[start, end)` interval test detects overlapping time slots for the same pet or across pets, and returns warning strings instead of crashing. |
| Recurring tasks | `CareTask.next_occurrence()`, `Pet.complete_task()` | Completing a `DAILY`/`WEEKLY` task auto-creates the next instance using `timedelta` (today + 1 day / + 1 week); one-off tasks return `None`. |

### How the daily plan is built (`Scheduler.build_plan()`)

1. Drop completed tasks; keep what's pending.
2. Place `fixed_time` tasks at their pinned slots first.
3. Greedily fill the remaining `available_minutes` with the rest, ordered by
   priority then shortest duration; anything that doesn't fit goes to `skipped`.
4. Attach a plain-language `explanation` of what was scheduled and why.

## Demo Walkthrough

### Main UI features (Streamlit app: `streamlit run app.py`)

- **Owner & Pet panel** — enter the owner's name, the pet's name/species, and the total minutes available today. Owner and pet objects persist across reruns via `st.session_state`.
- **Task entry** — add a task with a title, duration, and priority, plus an optional **fixed start time** and a **repeat** setting (none / daily / weekly).
- **Current tasks** — a table that can be **filtered** to pending-only and is **sorted chronologically**; you can mark a task complete, which auto-adds the next occurrence for recurring tasks.
- **Build Schedule** — generates the day's plan with summary metrics (scheduled / minutes used / skipped), a time-ordered table, a plain-language explanation, skipped-task warnings, and **conflict alerts**.

### Example workflow

1. **Add a pet** — set Owner = "Jordan", Pet = "Mochi" (dog), and available minutes = 90.
2. **Schedule tasks** — add "Morning walk" (30 min, high), "Give meds" (5 min, high) with a fixed time of 08:00, and "Grooming" (40 min, low).
3. **View today's schedule** — click **Generate schedule**: the fixed-time meds land at 08:00, the high-priority walk fills from the start of the day, and lower-priority grooming is skipped if it doesn't fit the 90 minutes.
4. **Complete a recurring task** — mark a daily task done and watch its next-day occurrence appear automatically.

### Key Scheduler behaviors shown

- **Sorting** — fixed-time tasks placed at their slot; remaining tasks ordered by priority then duration; the plan table is chronological.
- **Filtering** — completed tasks drop out of both the task list and new plans.
- **Conflict warnings** — overlapping time slots (e.g. two pets both at 08:00) are reported, not crashed on.
- **Recurrence** — daily/weekly tasks regenerate on completion.

### Sample CLI output (`python main.py`)

```
============================================================
TODAY'S SCHEDULES

Mochi:
  07:00-07:30  Morning walk (30 min)
  08:00-08:15  Give meds (15 min)

Biscuit:
  07:00-07:10  Litter cleanup (10 min)
  08:00-08:10  Feed breakfast (10 min)

============================================================
CONFLICT CHECK
  WARNING: 'Morning walk' (Mochi) overlaps 'Litter cleanup' (Biscuit) around 07:00 [Mochi vs Biscuit].
  WARNING: 'Give meds' (Mochi) overlaps 'Feed breakfast' (Biscuit) around 08:00 [Mochi vs Biscuit].
```
