"""Tests for PawPal+ scheduling behaviors."""

from datetime import date, time

import pytest

from pawpal_system import (
    CareTask,
    DailyPlan,
    Owner,
    Pet,
    Priority,
    Recurrence,
    ScheduledTask,
    Scheduler,
)


# --- Model basics -----------------------------------------------------------

def test_owner_add_pet():
    owner = Owner(name="Jordan")
    pet = Pet(name="Mochi", species="dog")
    owner.add_pet(pet)
    assert owner.pets == [pet]


def test_pet_add_and_remove_task():
    pet = Pet(name="Mochi", species="dog")
    walk = CareTask("Walk", 20, Priority.HIGH)
    pet.add_task(walk)
    assert pet.tasks == [walk]
    pet.remove_task("Walk")
    assert pet.tasks == []


def test_adding_task_increases_pet_task_count():
    pet = Pet(name="Mochi", species="dog")
    assert len(pet.tasks) == 0
    pet.add_task(CareTask("Walk", 20, Priority.HIGH))
    assert len(pet.tasks) == 1
    pet.add_task(CareTask("Feed", 10, Priority.HIGH))
    assert len(pet.tasks) == 2


def test_mark_complete_changes_task_status():
    task = CareTask("Walk", 20, Priority.HIGH)
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


# --- sort_tasks --------------------------------------------------------------

def test_sort_tasks_orders_by_priority_then_shortest():
    scheduler = Scheduler(Owner(name="J"))
    tasks = [
        CareTask("low-long", 30, Priority.LOW),
        CareTask("high-long", 40, Priority.HIGH),
        CareTask("high-short", 10, Priority.HIGH),
        CareTask("med", 15, Priority.MEDIUM),
    ]
    ordered = [t.title for t in scheduler.sort_tasks(tasks)]
    assert ordered == ["high-short", "high-long", "med", "low-long"]


# --- fits --------------------------------------------------------------------

@pytest.mark.parametrize(
    "duration, remaining, expected",
    [(20, 30, True), (30, 30, True), (31, 30, False), (0, 30, False)],
)
def test_fits(duration, remaining, expected):
    scheduler = Scheduler(Owner(name="J"))
    assert scheduler.fits(CareTask("t", duration), remaining) is expected


# --- build_plan --------------------------------------------------------------

def test_build_plan_skips_tasks_over_budget():
    owner = Owner(name="J", available_minutes=30)
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(CareTask("Walk", 20, Priority.HIGH))
    pet.add_task(CareTask("Grooming", 40, Priority.LOW))

    plan = Scheduler(owner).build_plan(pet)

    scheduled_titles = [s.task.title for s in plan.scheduled]
    skipped_titles = [t.title for t in plan.skipped]
    assert scheduled_titles == ["Walk"]
    assert skipped_titles == ["Grooming"]
    assert plan.total_minutes == 20


def test_build_plan_prefers_high_priority_when_time_is_tight():
    owner = Owner(name="J", available_minutes=20)
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(CareTask("Low task", 20, Priority.LOW))
    pet.add_task(CareTask("High task", 20, Priority.HIGH))

    plan = Scheduler(owner).build_plan(pet)

    assert [s.task.title for s in plan.scheduled] == ["High task"]
    assert [t.title for t in plan.skipped] == ["Low task"]


def test_build_plan_places_fixed_time_task_at_its_time():
    owner = Owner(name="J", wake_hour=7, available_minutes=120)
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(CareTask("Meds", 5, Priority.HIGH, fixed_time=time(8, 0)))
    pet.add_task(CareTask("Walk", 30, Priority.HIGH))

    plan = Scheduler(owner).build_plan(pet)

    meds = next(s for s in plan.scheduled if s.task.title == "Meds")
    assert meds.start_minute == 8 * 60
    assert meds.end_minute == 8 * 60 + 5
    # Flexible task starts at wake_hour.
    walk = next(s for s in plan.scheduled if s.task.title == "Walk")
    assert walk.start_minute == 7 * 60


def test_build_plan_empty_pet_produces_empty_plan():
    plan = Scheduler(Owner(name="J")).build_plan(Pet(name="Mochi", species="dog"))
    assert plan.scheduled == []
    assert plan.skipped == []
    assert plan.total_minutes == 0


# --- summary / explain -------------------------------------------------------

def test_summary_includes_task_and_total():
    owner = Owner(name="J", available_minutes=60)
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(CareTask("Walk", 20, Priority.HIGH))

    summary = Scheduler(owner).build_plan(pet).summary()
    assert "Walk" in summary
    assert "Total: 20 min" in summary


def test_explain_reports_skipped_count():
    owner = Owner(name="J", available_minutes=10)
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(CareTask("Walk", 20, Priority.HIGH))

    plan = Scheduler(owner).build_plan(pet)
    assert "Skipped 1" in plan.explanation


# --- filtering ---------------------------------------------------------------

def test_pending_tasks_excludes_completed():
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(CareTask("Walk", 20, Priority.HIGH))
    done = CareTask("Feed", 10, Priority.HIGH)
    pet.add_task(done)
    done.mark_complete()

    titles = [t.title for t in pet.pending_tasks()]
    assert titles == ["Walk"]


def test_owner_filter_tasks_by_pet_name_and_status():
    owner = Owner(name="J")
    mochi = Pet(name="Mochi", species="dog")
    biscuit = Pet(name="Biscuit", species="cat")
    owner.add_pet(mochi)
    owner.add_pet(biscuit)
    mochi.add_task(CareTask("Walk", 20, Priority.HIGH))
    biscuit.add_task(CareTask("Feed", 10, Priority.HIGH))

    assert [t.title for t in owner.filter_tasks(pet_name="Mochi")] == ["Walk"]
    assert len(owner.filter_tasks(completed=False)) == 2
    assert owner.filter_tasks(completed=True) == []


# --- sort_by_time ------------------------------------------------------------

def test_sort_by_time_orders_timed_then_flexible():
    scheduler = Scheduler(Owner(name="J"))
    tasks = [
        CareTask("flex", 10),
        CareTask("evening", 10, fixed_time=time(18, 0)),
        CareTask("morning", 10, fixed_time=time(8, 0)),
    ]
    assert [t.title for t in scheduler.sort_by_time(tasks)] == ["morning", "evening", "flex"]


# --- recurrence --------------------------------------------------------------

def test_daily_task_regenerates_next_day():
    task = CareTask("Walk", 20, recurrence=Recurrence.DAILY, due_date=date(2026, 6, 25))
    nxt = task.mark_complete()
    assert task.completed is True
    assert nxt is not None
    assert nxt.due_date == date(2026, 6, 26)
    assert nxt.completed is False


def test_weekly_task_regenerates_seven_days_later():
    task = CareTask("Groom", 40, recurrence=Recurrence.WEEKLY, due_date=date(2026, 6, 25))
    assert task.mark_complete().due_date == date(2026, 7, 2)


def test_non_recurring_task_returns_no_next_occurrence():
    assert CareTask("Vet", 60).mark_complete() is None


def test_pet_complete_task_auto_adds_next_occurrence():
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(CareTask("Walk", 20, recurrence=Recurrence.DAILY, due_date=date(2026, 6, 25)))
    pet.complete_task("Walk")
    assert len(pet.tasks) == 2
    assert [t.title for t in pet.pending_tasks()] == ["Walk"]


# --- conflict detection ------------------------------------------------------

def test_scheduled_task_overlaps():
    a = ScheduledTask(CareTask("A", 30), 480, 510)  # 08:00-08:30
    b = ScheduledTask(CareTask("B", 30), 500, 530)  # 08:20-08:50
    c = ScheduledTask(CareTask("C", 30), 510, 540)  # 08:30-09:00 (touches, no overlap)
    assert a.overlaps(b) is True
    assert a.overlaps(c) is False


def test_find_conflicts_flags_same_time_across_pets():
    owner = Owner(name="J", available_minutes=120)
    mochi = Pet(name="Mochi", species="dog")
    biscuit = Pet(name="Biscuit", species="cat")
    owner.add_pet(mochi)
    owner.add_pet(biscuit)
    mochi.add_task(CareTask("Meds", 15, Priority.HIGH, fixed_time=time(8, 0)))
    biscuit.add_task(CareTask("Feed", 10, Priority.HIGH, fixed_time=time(8, 0)))

    scheduler = Scheduler(owner)
    plans = {p.name: scheduler.build_plan(p) for p in owner.pets}
    warnings = scheduler.find_conflicts(plans)
    assert len(warnings) == 1
    assert "Meds" in warnings[0] and "Feed" in warnings[0]


def test_no_conflicts_when_tasks_are_spaced():
    owner = Owner(name="J", available_minutes=120)
    pet = Pet(name="Mochi", species="dog")
    owner.add_pet(pet)
    pet.add_task(CareTask("Meds", 15, Priority.HIGH, fixed_time=time(8, 0)))
    pet.add_task(CareTask("Walk", 15, Priority.HIGH, fixed_time=time(9, 0)))

    scheduler = Scheduler(owner)
    plans = {pet.name: scheduler.build_plan(pet)}
    assert scheduler.find_conflicts(plans) == []
