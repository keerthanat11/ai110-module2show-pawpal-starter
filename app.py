import streamlit as st

from pawpal_system import CareTask, DailyPlan, Owner, Pet, Priority, ScheduledTask, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

st.subheader("Owner & Pet")
owner_name = st.text_input("Owner name", value="Jordan")
pet_name = st.text_input("Pet name", value="Mochi")
species = st.selectbox("Species", ["dog", "cat", "other"])
available = st.number_input(
    "Minutes available today", min_value=10, max_value=600, value=90, step=10
)

# Persist the Owner object across reruns: create it once, then reuse it.
# Without this guard, every button click would rebuild an empty Owner.
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name=owner_name)
owner = st.session_state.owner
owner.name = owner_name
owner.available_minutes = int(available)

# Persist a single Pet attached to the owner (created once, then reused).
if "pet" not in st.session_state:
    st.session_state.pet = Pet(name=pet_name, species=species)
    owner.add_pet(st.session_state.pet)
pet = st.session_state.pet
pet.name = pet_name
pet.species = species

st.markdown("### Tasks")
st.caption("Add tasks to your pet. These feed directly into the scheduler.")

PRIORITY_MAP = {"low": Priority.LOW, "medium": Priority.MEDIUM, "high": Priority.HIGH}

col1, col2, col3 = st.columns(3)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
with col3:
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

# Replace the placeholder dict-append with a real CareTask + Pet.add_task() call.
if st.button("Add task"):
    pet.add_task(CareTask(task_title, int(duration), PRIORITY_MAP[priority]))

if pet.tasks:
    st.write("Current tasks:")
    st.table(
        [
            {
                "title": t.title,
                "duration_minutes": t.duration_minutes,
                "priority": t.priority.name.lower(),
            }
            for t in pet.tasks
        ]
    )
else:
    st.info("No tasks yet. Add one above.")

st.divider()

st.subheader("Build Schedule")
st.caption("Calls Scheduler.build_plan() on your pet's tasks.")

# Replace the placeholder warning with a real call into the scheduling logic.
if st.button("Generate schedule"):
    scheduler = Scheduler(owner)
    plan = scheduler.build_plan(pet)
    st.markdown(f"#### Today's plan for {pet.name} ({pet.species})")

    if plan.scheduled:
        st.table(
            [
                {
                    "start": f"{s.as_times()[0]:%H:%M}",
                    "end": f"{s.as_times()[1]:%H:%M}",
                    "task": s.task.title,
                    "min": s.task.duration_minutes,
                    "priority": s.task.priority.name.lower(),
                    "why": s.reason,
                }
                for s in sorted(plan.scheduled, key=lambda s: s.start_minute)
            ]
        )
    else:
        st.info("No tasks could be scheduled.")

    st.success(plan.explanation)

    if plan.skipped:
        st.warning(
            "Skipped (out of time): "
            + ", ".join(f"{t.title} ({t.duration_minutes} min)" for t in plan.skipped)
        )

    # Lightweight conflict check: warn on overlapping time slots (don't crash).
    for conflict in scheduler.find_conflicts({pet.name: plan}):
        st.error(conflict)
