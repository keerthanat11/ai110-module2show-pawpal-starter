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
from datetime import date, time
from enum import IntEnum
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
    recurring: bool = False
    completed: bool = False

    def mark_complete(self) -> None:
        """Mark this task as done."""
        self.completed = True


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

        fixed = sorted(
            (t for t in pet.tasks if t.fixed_time is not None),
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
        for task in self.sort_tasks([t for t in pet.tasks if t.fixed_time is None]):
            if not self.fits(task, remaining):
                plan.skipped.append(task)
                continue
            plan.scheduled.append(
                ScheduledTask(task, cursor, cursor + task.duration_minutes,
                              reason=f"{task.priority.name.lower()} priority")
            )
            cursor += task.duration_minutes
            remaining -= task.duration_minutes

        plan.total_minutes = sum(s.task.duration_minutes for s in plan.scheduled)
        plan.explanation = self.explain(plan)
        return plan

    def sort_tasks(self, tasks: List[CareTask]) -> List[CareTask]:
        """Order tasks by priority (high first), then shortest duration first."""
        return sorted(tasks, key=lambda t: (-int(t.priority), t.duration_minutes))

    def fits(self, task: CareTask, remaining: int) -> bool:
        """Return True if the task fits in the remaining available minutes."""
        return 0 < task.duration_minutes <= remaining

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
