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
- If yes, describe at least one change and why you made it.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
