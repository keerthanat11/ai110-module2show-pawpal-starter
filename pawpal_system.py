"""PawPal+ logic layer — backend classes for pet care planning.

This is the skeleton translated from diagrams/uml.mmd. Signatures, attributes,
and docstrings are defined here; the scheduling logic is implemented later.

Data objects (Pet, CareTask, Owner, ScheduledTask, DailyPlan) use Python
dataclasses to keep them clean — no hand-written __init__ boilerplate.

Design overview (three core user actions):
    1. Add a pet & its care tasks  -> Owner.add_pet, Pet.add_task/remove_task, CareTask
    2. Generate today's plan        -> Scheduler.build_plan -> DailyPlan
    3. See today's tasks & why      -> DailyPlan.summary, ScheduledTask.reason, Scheduler.explain
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, time, timedelta
from enum import Enum, IntEnum
from typing import List, Optional


def _to_time(minute: int) -> time:
    """Convert minutes-from-midnight to a datetime.time (wraps past 24h)."""
    minute %= 24 * 60
    return time(minute // 60, minute % 60)


class Priority(IntEnum):
    """Importance level of a care task. IntEnum so tasks sort by priority directly."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3


class Recurrence(Enum):
    """How often a task repeats."""

    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"


@dataclass
class CareTask:
    """A single thing the owner needs to do for the pet (walk, feeding, meds, ...).

    fixed_time pins the task to a specific start; flexible tasks (fixed_time=None)
    are packed into whatever time remains.
    """

    title: str
    duration_minutes: int
    priority: Priority = Priority.MEDIUM
    category: str = "general"
    fixed_time: Optional[time] = None
    recurrence: Recurrence = Recurrence.NONE
    due_date: Optional[date] = None
    completed: bool = False

    def mark_complete(self) -> Optional["CareTask"]:
        """Mark this task done; if it recurs, return a fresh instance for next time."""
        self.completed = True
        return self.next_occurrence()

    def next_occurrence(self) -> Optional["CareTask"]:
        """Build the next instance of a recurring task.

        Advances the due date by one step from this task's due_date (or today if
        unset): timedelta(days=1) for DAILY, timedelta(weeks=1) for WEEKLY, which
        handles month/year rollovers correctly.

        Returns:
            A fresh, uncompleted CareTask for the next date, or None if the task
            does not recur (Recurrence.NONE).
        """
        if self.recurrence is Recurrence.NONE:
            return None
        step = timedelta(days=1) if self.recurrence is Recurrence.DAILY else timedelta(weeks=1)
        base = self.due_date or date.today()
        return CareTask(
            title=self.title,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            category=self.category,
            fixed_time=self.fixed_time,
            recurrence=self.recurrence,
            due_date=base + step,
        )


@dataclass
class Pet:
    """Basic pet info plus the list of its care tasks."""

    name: str
    species: str
    breed: str = ""
    age_years: int = 0
    notes: str = ""
    tasks: List[CareTask] = field(default_factory=list)

    def add_task(self, task: CareTask) -> None:
        """Add a care task to this pet."""
        self.tasks.append(task)

    def remove_task(self, title: str) -> None:
        """Remove a care task from this pet by its title."""
        self.tasks = [t for t in self.tasks if t.title != title]

    def pending_tasks(self) -> List[CareTask]:
        """Return only this pet's tasks that are not yet completed."""
        return [t for t in self.tasks if not t.completed]

    def complete_task(self, title: str) -> Optional[CareTask]:
        """Mark a task done; auto-add and return its next occurrence if it recurs."""
        for task in self.tasks:
            if task.title == title and not task.completed:
                upcoming = task.mark_complete()
                if upcoming is not None:
                    self.tasks.append(upcoming)
                return upcoming
        return None


@dataclass
class Owner:
    """The human and their scheduling constraints/preferences.

    available_minutes is the single authoritative time budget; wake_hour is only
    the clock time the day starts at.
    """

    name: str
    wake_hour: int = 7
    available_minutes: int = 120
    preferences: List[str] = field(default_factory=list)
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Register a pet under this owner."""
        self.pets.append(pet)

    def filter_tasks(
        self, pet_name: Optional[str] = None, completed: Optional[bool] = None
    ) -> List[CareTask]:
        """Return tasks across pets, optionally filtered by pet name and/or status."""
        tasks: List[CareTask] = []
        for pet in self.pets:
            if pet_name is not None and pet.name != pet_name:
                continue
            for task in pet.tasks:
                if completed is not None and task.completed != completed:
                    continue
                tasks.append(task)
        return tasks


@dataclass
class ScheduledTask:
    """A CareTask placed on the clock, with the reason it was scheduled.

    Times are stored as minutes-from-midnight (ints) to avoid datetime.time
    arithmetic; as_times() formats them for display.
    """

    task: CareTask
    start_minute: int
    end_minute: int
    reason: str = ""

    def as_times(self) -> tuple[time, time]:
        """Return (start, end) as datetime.time for display."""
        return (_to_time(self.start_minute), _to_time(self.end_minute))

    def overlaps(self, other: "ScheduledTask") -> bool:
        """Return True if this task's time interval overlaps another's.

        Uses the half-open interval test [start, end): two ranges overlap iff
        each starts before the other ends. Tasks that merely touch (one ends
        exactly when the next begins) do NOT count as overlapping.
        """
        return self.start_minute < other.end_minute and other.start_minute < self.end_minute


@dataclass
class DailyPlan:
    """The result of scheduling: what got placed, what was skipped, and why."""

    day: date
    scheduled: List[ScheduledTask] = field(default_factory=list)
    skipped: List[CareTask] = field(default_factory=list)
    total_minutes: int = 0
    explanation: str = ""

    def summary(self) -> str:
        """Render a human-readable summary of the plan for display."""
        lines: List[str] = []
        for st in sorted(self.scheduled, key=lambda s: s.start_minute):
            start, end = st.as_times()
            lines.append(
                f"  {start:%H:%M}-{end:%H:%M}  {st.task.title} "
                f"({st.task.duration_minutes} min) [priority: {st.task.priority.name.lower()}]"
            )
        if self.skipped:
            lines.append("  Skipped (out of time):")
            for task in self.skipped:
                lines.append(f"    - {task.title} ({task.duration_minutes} min)")
        body = "\n".join(lines) if lines else "  (no tasks)"
        return f"{body}\n  Total: {self.total_minutes} min planned"


class Scheduler:
    """The 'brain': turns a pet's tasks + owner constraints into a DailyPlan."""

    def __init__(self, owner: Owner, day_start_hour: Optional[int] = None) -> None:
        """Bind the scheduler to an owner and the clock hour the day starts at."""
        self.owner = owner
        self.day_start_hour = day_start_hour if day_start_hour is not None else owner.wake_hour

    def build_plan(self, pet: Pet, day: Optional[date] = None) -> DailyPlan:
        """Place fixed-time tasks, then fill remaining minutes by priority."""
        plan = DailyPlan(day=day or date.today())
        remaining = self.owner.available_minutes

        # Only plan tasks that aren't already done.
        pending = pet.pending_tasks()

        fixed = sorted(
            (t for t in pending if t.fixed_time is not None),
            key=lambda t: t.fixed_time.hour * 60 + t.fixed_time.minute,
        )
        for task in fixed:
            if not self.fits(task, remaining):
                plan.skipped.append(task)
                continue
            start = task.fixed_time.hour * 60 + task.fixed_time.minute
            plan.scheduled.append(
                ScheduledTask(task, start, start + task.duration_minutes,
                              reason=f"fixed at {task.fixed_time:%H:%M}")
            )
            remaining -= task.duration_minutes

        cursor = self.day_start_hour * 60
        for task in self.sort_tasks([t for t in pending if t.fixed_time is None]):
            if not self.fits(task, remaining):
                plan.skipped.append(task)
                continue
            plan.scheduled.append(
                ScheduledTask(task, cursor, cursor + task.duration_minutes,
                              reason=f"{task.priority.name.lower()} priority")
            )
            cursor += task.duration_minutes
            remaining -= task.duration_minutes

        plan.scheduled.sort(key=lambda s: s.start_minute)  # keep the plan chronological
        plan.total_minutes = sum(s.task.duration_minutes for s in plan.scheduled)
        plan.explanation = self.explain(plan)
        return plan

    def sort_tasks(self, tasks: List[CareTask]) -> List[CareTask]:
        """Order tasks by priority (high first), then shortest duration first."""
        return sorted(tasks, key=lambda t: (-int(t.priority), t.duration_minutes))

    def sort_by_time(self, tasks: List[CareTask]) -> List[CareTask]:
        """Order tasks chronologically by fixed_time, with flexible tasks last.

        Sorts on a tuple key (has-no-time?, the-time): False sorts before True,
        so fixed-time tasks come first in clock order while flexible tasks
        (fixed_time is None) fall to the end. The tuple avoids comparing None to
        a time, which would raise TypeError.

        Args:
            tasks: The tasks to order (not mutated).

        Returns:
            A new list sorted by time of day.
        """
        return sorted(tasks, key=lambda t: (t.fixed_time is None, t.fixed_time or time.min))

    def fits(self, task: CareTask, remaining: int) -> bool:
        """Return True if the task fits in the remaining available minutes."""
        return 0 < task.duration_minutes <= remaining

    def find_conflicts(self, plans: dict) -> List[str]:
        """Return warning strings for overlapping scheduled tasks across plans.

        Flattens every plan's scheduled tasks into one (label, task) list, then
        does a lightweight pairwise O(n^2) scan comparing each pair with
        ScheduledTask.overlaps. Catches both same-pet and cross-pet clashes.
        Returns messages instead of raising, so callers keep running.

        Args:
            plans: Mapping of label (e.g. pet name) -> DailyPlan.

        Returns:
            A list of human-readable warning strings; empty if no conflicts.
        """
        entries = [(label, st) for label, plan in plans.items() for st in plan.scheduled]
        warnings: List[str] = []
        for i in range(len(entries)):
            for j in range(i + 1, len(entries)):
                (label_a, a), (label_b, b) = entries[i], entries[j]
                if a.overlaps(b):
                    start, _ = a.as_times()
                    same = "same pet" if label_a == label_b else f"{label_a} vs {label_b}"
                    warnings.append(
                        f"WARNING: '{a.task.title}' ({label_a}) overlaps "
                        f"'{b.task.title}' ({label_b}) around {start:%H:%M} [{same}]."
                    )
        return warnings

    def explain(self, plan: DailyPlan) -> str:
        """Compose the per-task reasons into a single plan-level explanation."""
        placed = len(plan.scheduled)
        skipped = len(plan.skipped)
        parts = [f"Placed {placed} task(s) using {plan.total_minutes} of "
                 f"{self.owner.available_minutes} available minutes."]
        if skipped:
            parts.append(f"Skipped {skipped} task(s) once time ran out, "
                         f"keeping higher-priority tasks first.")
        return " ".join(parts)
