from datetime import time

import streamlit as st

from pawpal_system import CareTask, Owner, Pet, Priority, Recurrence, Scheduler

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

scheduler = Scheduler(owner)

PRIORITY_MAP = {"low": Priority.LOW, "medium": Priority.MEDIUM, "high": Priority.HIGH}
RECUR_MAP = {"none": Recurrence.NONE, "daily": Recurrence.DAILY, "weekly": Recurrence.WEEKLY}

st.markdown("### Tasks")
st.caption("Add tasks to your pet. These feed directly into the scheduler.")

col1, col2, col3 = st.columns(3)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
with col3:
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

col4, col5 = st.columns(2)
with col4:
    has_time = st.checkbox("Fixed start time?")
    fixed_time = st.time_input("Start time", value=time(8, 0)) if has_time else None
with col5:
    repeats = st.selectbox("Repeats", ["none", "daily", "weekly"])

# Build a real CareTask and attach it via Pet.add_task().
if st.button("Add task"):
    pet.add_task(
        CareTask(
            task_title,
            int(duration),
            PRIORITY_MAP[priority],
            fixed_time=fixed_time,
            recurrence=RECUR_MAP[repeats],
        )
    )

# --- Current tasks: filtered by status, sorted chronologically --------------
show_pending = st.checkbox("Show only pending tasks")
visible = pet.pending_tasks() if show_pending else pet.tasks  # Pet/Owner filtering

if visible:
    st.write("Current tasks (sorted by time):")
    st.table(
        [
            {
                "when": f"{t.fixed_time:%H:%M}" if t.fixed_time else "flexible",
                "task": t.title,
                "min": t.duration_minutes,
                "priority": t.priority.name.lower(),
                "repeats": t.recurrence.value,
                "status": "done" if t.completed else "todo",
            }
            for t in scheduler.sort_by_time(visible)  # Scheduler.sort_by_time()
        ]
    )

    # Completing a recurring task auto-adds its next occurrence.
    done_title = st.selectbox("Mark a task complete", [t.title for t in pet.pending_tasks()] or ["—"])
    if st.button("Complete task") and done_title != "—":
        upcoming = pet.complete_task(done_title)
        if upcoming is not None:
            st.success(f"Completed '{done_title}'. Next occurrence added for {upcoming.due_date}.")
        else:
            st.success(f"Completed '{done_title}'.")
        st.rerun()
else:
    st.info("No tasks to show. Add one above.")

st.divider()

st.subheader("Build Schedule")
st.caption("Calls Scheduler.build_plan() on your pet's tasks.")

if st.button("Generate schedule"):
    plan = scheduler.build_plan(pet)
    st.markdown(f"#### Today's plan for {pet.name} ({pet.species})")

    # Summary metrics for a professional, at-a-glance view.
    m1, m2, m3 = st.columns(3)
    m1.metric("Scheduled", len(plan.scheduled))
    m2.metric("Minutes used", f"{plan.total_minutes} / {owner.available_minutes}")
    m3.metric("Skipped", len(plan.skipped))

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
                for s in plan.scheduled  # build_plan already returns these in time order
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
    conflicts = scheduler.find_conflicts({pet.name: plan})
    for conflict in conflicts:
        st.error(conflict)
    if not conflicts and plan.scheduled:
        st.caption("✅ No scheduling conflicts detected.")
