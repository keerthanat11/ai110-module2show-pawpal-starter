"""Tests for PawPal+ scheduling behaviors."""

from datetime import time

import pytest

from pawpal_system import CareTask, DailyPlan, Owner, Pet, Priority, Scheduler


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
