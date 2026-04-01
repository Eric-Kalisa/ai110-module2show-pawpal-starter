from datetime import date

from pawpal_system import Owner, Pet, Scheduler, Task


def test_mark_complete_changes_task_status() -> None:
	task = Task(description="Morning walk", time="07:30", frequency="Daily")

	task.mark_complete()

	assert task.completed is True


def test_adding_task_increases_pet_task_count() -> None:
	pet = Pet(name="Mochi", species="Dog", age=4)
	task = Task(description="Dinner", time="18:00", frequency="Daily")

	starting_count = len(pet.tasks)
	pet.add_task(task)

	assert len(pet.tasks) == starting_count + 1


def test_scheduler_sorts_tasks_by_time() -> None:
	owner = Owner(name="Jordan")
	pet = Pet(name="Mochi", species="Dog", age=4)
	pet.add_task(Task(description="Dinner", time="18:00", frequency="Daily"))
	pet.add_task(Task(description="Walk", time="07:30", frequency="Daily"))
	owner.add_pet(pet)
	scheduler = Scheduler(owner)

	sorted_tasks = scheduler.sort_tasks_by_time()

	assert [item["task"].description for item in sorted_tasks] == ["Walk", "Dinner"]


def test_scheduler_filters_by_pet_and_status() -> None:
	owner = Owner(name="Jordan")
	mochi = Pet(name="Mochi", species="Dog", age=4)
	luna = Pet(name="Luna", species="Cat", age=2)

	walk = Task(description="Walk", time="07:30", frequency="Daily")
	dinner = Task(description="Dinner", time="18:00", frequency="Daily")
	brush = Task(description="Brush", time="20:00", frequency="Weekly")
	dinner.mark_complete()

	mochi.add_task(walk)
	mochi.add_task(dinner)
	luna.add_task(brush)
	owner.add_pet(mochi)
	owner.add_pet(luna)
	scheduler = Scheduler(owner)

	filtered = scheduler.filter_tasks(pet_name="Mochi", status="completed")

	assert len(filtered) == 1
	assert filtered[0]["task"].description == "Dinner"


def test_recurring_tasks_occurrence_by_date() -> None:
	task_daily = Task(
		description="Daily meal",
		time="08:00",
		frequency="Daily",
		starts_on=date(2026, 3, 1),
	)
	task_weekly = Task(
		description="Weekly grooming",
		time="09:00",
		frequency="Weekly",
		starts_on=date(2026, 3, 2),  # Monday
	)
	task_monthly = Task(
		description="Monthly meds",
		time="10:00",
		frequency="Monthly",
		starts_on=date(2026, 3, 15),
	)

	assert task_daily.occurs_on(date(2026, 3, 10)) is True
	assert task_weekly.occurs_on(date(2026, 3, 9)) is True  # Monday
	assert task_weekly.occurs_on(date(2026, 3, 10)) is False
	assert task_monthly.occurs_on(date(2026, 4, 15)) is True
	assert task_monthly.occurs_on(date(2026, 4, 14)) is False


def test_pet_add_task_detects_time_conflict() -> None:
	pet = Pet(name="Mochi", species="Dog", age=4)
	pet.add_task(Task(description="Morning walk", time="07:30", frequency="Daily"))

	warning_message = pet.add_task(Task(description="Breakfast", time="07:30", frequency="Daily"))

	assert warning_message is not None
	assert "Task conflict for Mochi" in warning_message
	assert len(pet.tasks) == 1


def test_pet_add_task_detects_duration_overlap_with_clear_message() -> None:
	pet = Pet(name="Mochi", species="Dog", age=4)
	pet.add_task(
		Task(
			description="Long walk",
			time="07:30",
			frequency="Daily",
			duration_minutes=60,
			priority="High",
		)
	)

	warning_message = pet.add_task(
		Task(
			description="Breakfast",
			time="08:00",
			frequency="Daily",
			duration_minutes=30,
			priority="Low",
		)
	)

	assert warning_message is not None
	assert "not enough time to complete both activities" in warning_message
	assert "Recommended activity to complete first: 'Long walk'" in warning_message
	assert len(pet.tasks) == 1


def test_conflict_recommendation_prefers_new_task_when_higher_priority() -> None:
	pet = Pet(name="Mochi", species="Dog", age=4)
	pet.add_task(
		Task(
			description="Low priority enrichment",
			time="07:30",
			frequency="Daily",
			duration_minutes=60,
			priority="Low",
		)
	)

	warning_message = pet.add_task(
		Task(
			description="Medication",
			time="08:00",
			frequency="Daily",
			duration_minutes=30,
			priority="High",
		)
	)

	assert warning_message is not None
	assert "Recommended activity to complete first: 'Medication'" in warning_message


def test_scheduler_detects_cross_pet_conflicts() -> None:
	owner = Owner(name="Jordan")
	mochi = Pet(name="Mochi", species="Dog", age=4)
	luna = Pet(name="Luna", species="Cat", age=2)

	mochi.add_task(Task(description="Walk", time="08:00", frequency="Daily"))
	luna.add_task(Task(description="Feed", time="08:00", frequency="Daily"))
	owner.add_pet(mochi)
	owner.add_pet(luna)
	scheduler = Scheduler(owner)

	conflicts = scheduler.detect_conflicts()

	assert len(conflicts) == 1
	assert conflicts[0]["time"] == "08:00"


def test_scheduler_detects_cross_pet_duration_overlap_conflicts() -> None:
	owner = Owner(name="Jordan")
	mochi = Pet(name="Mochi", species="Dog", age=4)
	luna = Pet(name="Luna", species="Cat", age=2)

	mochi.add_task(
		Task(description="Morning walk", time="08:00", frequency="Daily", duration_minutes=60)
	)
	luna.add_task(
		Task(description="Medication", time="08:30", frequency="Daily", duration_minutes=20)
	)
	owner.add_pet(mochi)
	owner.add_pet(luna)
	scheduler = Scheduler(owner)

	conflicts = scheduler.detect_conflicts()

	assert len(conflicts) == 1
	assert conflicts[0]["first_task"] == "Morning walk"
	assert conflicts[0]["second_task"] == "Medication"


def test_marking_daily_task_complete_spawns_next_occurrence() -> None:
	owner = Owner(name="Jordan")
	pet = Pet(name="Mochi", species="Dog", age=4)
	pet.add_task(
		Task(
			description="Walk",
			time="07:30",
			frequency="Daily",
			starts_on=date(2026, 3, 31),
		)
	)
	owner.add_pet(pet)
	scheduler = Scheduler(owner)

	marked = scheduler.mark_task_complete("Mochi", "Walk")

	assert marked is True
	assert len(pet.tasks) == 2
	next_task = pet.tasks[1]
	assert next_task.description == "Walk"
	assert next_task.completed is False
	assert next_task.starts_on == date(2026, 4, 1)


def test_marking_weekly_task_complete_spawns_next_occurrence() -> None:
	owner = Owner(name="Jordan")
	pet = Pet(name="Mochi", species="Dog", age=4)
	pet.add_task(
		Task(
			description="Groom",
			time="09:00",
			frequency="Weekly",
			starts_on=date(2026, 3, 31),
		)
	)
	owner.add_pet(pet)
	scheduler = Scheduler(owner)

	marked = scheduler.mark_task_complete("Mochi", "Groom")

	assert marked is True
	assert len(pet.tasks) == 2
	next_task = pet.tasks[1]
	assert next_task.description == "Groom"
	assert next_task.completed is False
	assert next_task.starts_on == date(2026, 4, 7)


def test_marking_monthly_task_complete_does_not_spawn_next_occurrence() -> None:
	owner = Owner(name="Jordan")
	pet = Pet(name="Mochi", species="Dog", age=4)
	pet.add_task(
		Task(
			description="Medication",
			time="10:00",
			frequency="Monthly",
			starts_on=date(2026, 3, 31),
		)
	)
	owner.add_pet(pet)
	scheduler = Scheduler(owner)

	marked = scheduler.mark_task_complete("Mochi", "Medication")

	assert marked is True
	assert len(pet.tasks) == 1
