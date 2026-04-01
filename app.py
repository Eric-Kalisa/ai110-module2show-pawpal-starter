import streamlit as st

from pawpal_system import Owner, Pet, Scheduler, Task


def get_or_create_owner(owner_name: str) -> Owner:
    if "owner" not in st.session_state:
        st.session_state.owner = Owner(name=owner_name.strip() or "Jordan")

    owner = st.session_state.owner
    cleaned_name = owner_name.strip()
    if cleaned_name:
        owner.name = cleaned_name
    return owner


def find_pet(owner: Owner, pet_name: str) -> Pet | None:
    cleaned_name = pet_name.strip().lower()
    for pet in owner.pets:
        if pet.name.lower() == cleaned_name:
            return pet
    return None

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

st.subheader("Owner")
owner_name = st.text_input("Owner name", value="Jordan")

owner = get_or_create_owner(owner_name)
scheduler = Scheduler(owner)
st.caption(f"Session owner loaded: {owner.name}")

st.divider()

st.subheader("Add a Pet")
st.caption("New pet submissions should be handled by Owner.add_pet().")

with st.form("add_pet_form"):
    new_pet_name = st.text_input("Pet name", value="Mochi")
    new_pet_species = st.selectbox("Species", ["dog", "cat", "other"])
    new_pet_age = st.number_input("Age", min_value=0, max_value=50, value=2)
    add_pet_submitted = st.form_submit_button("Add pet")

if add_pet_submitted:
    if not new_pet_name.strip():
        st.error("Pet name is required.")
    elif find_pet(owner, new_pet_name) is not None:
        st.warning("That pet already exists for this owner.")
    else:
        owner.add_pet(Pet(new_pet_name.strip(), new_pet_species, int(new_pet_age)))
        st.success(f"Added pet: {new_pet_name.strip()}")

if owner.pets:
    st.write("Current pets:")
    st.table(
        [
            {
                "name": pet.name,
                "species": pet.species,
                "age": pet.age,
                "task_count": len(pet.tasks),
            }
            for pet in owner.pets
        ]
    )
else:
    st.info("No pets added yet.")

st.divider()

st.subheader("Schedule a Task")
st.caption("Task submissions should be handled by Pet.add_task().")

if owner.pets:
    with st.form("add_task_form"):
        selected_pet_name = st.selectbox(
            "Choose pet",
            options=[pet.name for pet in owner.pets],
        )
        task_description = st.text_input("Task description", value="Morning walk")
        task_time = st.text_input("Task time", value="07:30")
        task_frequency = st.selectbox("Frequency", ["Daily", "Weekly", "Monthly"])
        add_task_submitted = st.form_submit_button("Schedule task")

    if add_task_submitted:
        selected_pet = find_pet(owner, selected_pet_name)
        if selected_pet is None:
            st.error("Choose a valid pet before adding a task.")
        else:
            try:
                warning_message = scheduler.schedule_task(
                    selected_pet_name,
                    Task(
                        description=task_description.strip(),
                        time=task_time.strip(),
                        frequency=task_frequency,
                    ),
                )
                if warning_message:
                    st.warning(warning_message)
                else:
                    st.success(f"Added task for {selected_pet.name}: {task_description.strip()}")
            except ValueError as error:
                st.error(str(error))
else:
    st.info("Add a pet first before scheduling tasks.")

st.divider()

st.subheader("Today's Schedule")
organized_tasks = scheduler.organize_tasks()

if organized_tasks:
    st.table(
        [
            {
                "pet": item["pet"],
                "time": item["task"].time,
                "task": item["task"].description,
                "frequency": item["task"].frequency,
                "completed": item["task"].completed,
            }
            for item in organized_tasks
        ]
    )
else:
    st.info("No scheduled tasks yet.")
