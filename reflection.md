# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.

My initial UML design (see `diagrams/uml.mmd`) is a class diagram organized around three core user actions: (1) add a pet and its care tasks, (2) generate today's plan, and (3) see today's tasks and the reasoning behind them. I separated the domain model (what the data *is*) from the scheduling logic (what the system *does*), so each class has a single clear responsibility.

- What classes did you include, and what responsibilities did you assign to each?

- Priority:Fixed set of importance levels (`LOW`, `MEDIUM`, `HIGH`) so priority is type-safe rather than a free-form string.
- Owner:Holds the human's info and constraints: name, wake/sleep hours, total `available_minutes`, and preferences. Owns one or more pets (`add_pet`).
- Pet: Basic pet info (name, species, breed, age, notes) and the list of its care tasks, which it can add/remove (`add_task`, `remove_task`).
- CareTask: A single thing to do (walk, feeding, meds, etc.): title, `duration_minutes`, `priority`, category, optional `fixed_time`, and whether it's `recurring`. Exposes `priority_weight()` so the scheduler can rank it numerically.
- Scheduler: The "brain." Given a pet's tasks and the owner's constraints, it sorts tasks (`sort_tasks`), checks whether each fits in the remaining time (`fits`), and assembles a `DailyPlan` (`build_plan`), including a human-readable rationale (`explain`).
- ScheduledTask: A task placed at a concrete `start_time`/`end_time`, plus the `reason` it was scheduled. Wraps a `CareTask` rather than duplicating its fields.
- DailyPlan: The output: the day, the list of scheduled tasks, any skipped tasks, total minutes used, and an explanation. `summary()` renders it for display.

Relationships: an `Owner` owns many `Pet`s; a `Pet` has many `CareTask`s; the `Scheduler` reads the `Owner`'s constraints and produces a `DailyPlan` composed of `ScheduledTask`s, each wrapping one `CareTask`.

**b. Design changes**

- Did your design change during implementation?

Yes. Reviewing the skeleton surfaced redundancies and ambiguities, so I tightened the design before adding logic.

- If yes, describe at least one change and why you made it.

- Dropped `CareTask.priority_weight()` — `Priority` is an `IntEnum`, so tasks sort directly without a second ranking that could drift.
- `build_plan(pet)` now reads `pet.tasks` instead of taking a separate `tasks` list, removing a duplicate source of truth.
- Made `Owner.available_minutes` the single time budget (removed `sleep_hour`), so `fits()` can't disagree with a wake/sleep window.
- `ScheduledTask` stores `start_minute`/`end_minute` as ints (minutes-from-midnight) instead of `time`, avoiding error-prone `datetime.time` math; `as_times()` formats for display.
- Defined `sort_tasks` tie-breaking (priority high-first, then shortest-first) and made `build_plan` place `fixed_time` tasks before filling flexible ones, so timing conflicts are handled deliberately.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?

Three: the owner's total available minutes (the time budget), each task's priority (high/medium/low), and fixed start times for tasks that must happen at a set time (e.g. meds at 8:00). It also tracks completion status so finished tasks aren't re-planned.

- How did you decide which constraints mattered most?

Time is the hard limit — nothing can be planned beyond the available minutes, so it gates everything. Within that budget, priority decides what gets cut first when time runs short, and fixed times are honored before flexible tasks so commitments aren't bumped.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.

It uses a greedy fill (highest priority first, shortest-duration to break ties) rather than searching for the mathematically optimal set of tasks.

- Why is that tradeoff reasonable for this scenario?

A daily pet routine has only a handful of tasks, and an owner cares more about "did the important things get done" than squeezing in the absolute maximum. Greedy is simple, fast, and easy to explain to the user — and the shortest-first tie-break still fits more tasks into leftover time.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?

I used AI across every phase: brainstorming the UML, generating class skeletons, implementing scheduling logic, writing tests, and wiring the Streamlit UI. It was most useful for turning a clear design into boilerplate quickly and for explaining concepts like `timedelta` and lambda sort keys.

- What kinds of prompts or questions were most helpful?

Specific, scoped prompts ("sort tasks by time, handle the `None` case", "lightweight conflict detection that warns instead of crashing") worked far better than vague ones. Asking it to *review* my skeleton for missing relationships also surfaced real issues early.

- Which AI coding assistant features were most effective for building your scheduler?

Inline code generation from a described method, the ability to run my tests/`main.py` and read the output, and review/critique of existing code. Letting it run `pytest` and report failures made the implement-test loop fast.

- How did using separate chat sessions for different phases help you stay organized?

Treating each phase (design → skeleton → logic → tests → UI → docs) as its own focused thread kept the context scoped to one concern at a time, so suggestions stayed relevant and I could verify each phase before moving to the next instead of mixing everything together.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.

The initial design included a `CareTask.priority_weight()` method and stored times as `datetime.time`. I rejected the redundant `priority_weight()` (since `Priority` is already an `IntEnum` that sorts directly) and switched `ScheduledTask` to integer minutes to avoid fragile `time` arithmetic.

- How did you evaluate or verify what the AI suggested?

I ran `main.py` to see real output, ran `pytest` after each change, and read the diffs rather than trusting blindly — for example, I caught that `build_plan` wasn't actually filtering completed tasks even though the docs claimed it did, and fixed it with a new test.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?

Sorting (by priority and by time), the time-budget `fits()` check and skipping when out of time, fixed-time placement, filtering by pet/status, completed-task exclusion, daily/weekly recurrence regeneration, and conflict detection (same-pet and cross-pet), plus negative cases like spaced tasks producing no conflicts.

- Why were these tests important?

These are the core decisions the scheduler makes — if sorting, fitting, or conflict logic is wrong, the daily plan is wrong. The negative cases matter just as much, since they prove the logic doesn't over-flag conflicts or over-generate recurring tasks.

**b. Confidence**

- How confident are you that your scheduler works correctly?

Fairly confident (about 4/5). All 27 tests pass and cover both positive and negative paths for every feature, and the live `main.py`/Streamlit output matches expectations.

- What edge cases would you test next if you had more time?

Month-end and leap-year recurrence, tasks scheduled past midnight, a shared (rather than per-pet) time budget across multiple pets, and the scheduler actively *resolving* conflicts rather than only reporting them.

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

The clean separation between the logic layer (`pawpal_system.py`) and the UI (`app.py`), and the test suite. Because the design was tightened before implementation, adding features like recurrence and conflict detection was straightforward.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

I'd make the scheduler *resolve* conflicts (shift flexible tasks into free gaps) instead of only warning, and support a shared household time budget across multiple pets rather than per-pet minutes.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

As the "lead architect," my judgment is what keeps the system coherent — AI generates fast and confidently, but it will happily add redundant methods or let docs drift from code. My job was to own the design decisions, scope each request, and verify everything by running tests and reading the output. The AI is a powerful implementer; the architecture, tradeoffs, and final sign-off stay with me.
