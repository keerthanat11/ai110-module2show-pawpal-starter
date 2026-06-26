"""Temporary testing ground for PawPal+ logic (run: python main.py)."""

from datetime import time

from pawpal_system import CareTask, Owner, Pet, Priority, Scheduler


def print_plan(label, plan):
    """Print a pet's scheduled tasks in time order."""
    print(f"\n{label}:")
    for s in sorted(plan.scheduled, key=lambda s: s.start_minute):
        start, end = s.as_times()
        print(f"  {start:%H:%M}-{end:%H:%M}  {s.task.title} ({s.task.duration_minutes} min)")


def main() -> None:
    owner = Owner(name="Jordan", wake_hour=7, available_minutes=120)

    mochi = Pet(name="Mochi", species="dog")
    biscuit = Pet(name="Biscuit", species="cat")
    owner.add_pet(mochi)
    owner.add_pet(biscuit)

    # Two tasks deliberately scheduled at the SAME time (08:00):
    #   - cross-pet: Mochi's meds and Biscuit's feeding both at 08:00
    mochi.add_task(CareTask("Give meds", 15, Priority.HIGH, fixed_time=time(8, 0)))
    biscuit.add_task(CareTask("Feed breakfast", 10, Priority.HIGH, fixed_time=time(8, 0)))

    # A few more tasks so the plans aren't trivial.
    mochi.add_task(CareTask("Morning walk", 30, Priority.HIGH))
    biscuit.add_task(CareTask("Litter cleanup", 10, Priority.MEDIUM))

    scheduler = Scheduler(owner)
    plans = {pet.name: scheduler.build_plan(pet) for pet in owner.pets}

    print("=" * 60)
    print("TODAY'S SCHEDULES")
    for name, plan in plans.items():
        print_plan(name, plan)

    print("\n" + "=" * 60)
    print("CONFLICT CHECK")
    warnings = scheduler.find_conflicts(plans)
    if warnings:
        for w in warnings:
            print(f"  {w}")
    else:
        print("  No conflicts found.")


if __name__ == "__main__":
    main()
