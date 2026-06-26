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

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
# Paste your pytest output here
```

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

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
