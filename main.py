"""Temporary testing ground for PawPal+ logic (run: python main.py)."""

from datetime import time

from pawpal_system import CareTask, Owner, Pet, Priority, Scheduler


def main() -> None:
    # 1. Create an owner.
    owner = Owner(name="Jordan", wake_hour=7, available_minutes=90)

    # 2. Create at least two pets and register them.
    mochi = Pet(name="Mochi", species="dog", breed="Shiba Inu", age_years=3)
    biscuit = Pet(name="Biscuit", species="cat", breed="Tabby", age_years=5)
    owner.add_pet(mochi)
    owner.add_pet(biscuit)

    # 3. Add at least three tasks with different times across the pets.
    mochi.add_task(CareTask("Morning walk", 30, Priority.HIGH))
    mochi.add_task(CareTask("Give meds", 5, Priority.HIGH, fixed_time=time(8, 0)))
    mochi.add_task(CareTask("Enrichment play", 25, Priority.MEDIUM))
    mochi.add_task(CareTask("Grooming", 40, Priority.LOW))

    biscuit.add_task(CareTask("Feed breakfast", 10, Priority.HIGH, fixed_time=time(7, 30)))
    biscuit.add_task(CareTask("Litter cleanup", 10, Priority.MEDIUM))
    biscuit.add_task(CareTask("Laser play", 15, Priority.LOW))

    # 4. Build and print today's schedule for each pet.
    scheduler = Scheduler(owner)
    print(f"Today's Schedule for {owner.name} "
          f"({owner.available_minutes} min available per pet)")
    print("=" * 60)
    for pet in owner.pets:
        plan = scheduler.build_plan(pet)
        print(f"\n{pet.name} ({pet.species}):")
        print(plan.summary())
        print(f"  Why: {plan.explanation}")


if __name__ == "__main__":
    main()
