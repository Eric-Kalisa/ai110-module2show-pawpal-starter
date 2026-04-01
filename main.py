from pawpal_system import Owner, Pet, Scheduler, Task


def build_sample_schedule() -> Scheduler:
	owner = Owner("Jordan")

	mochi = Pet(name="Mochi", species="Dog", age=4)
	luna = Pet(name="Luna", species="Cat", age=2)

	# Intentionally add tasks out of order to demonstrate sorting.
	mochi.add_task(Task(description="Dinner", time="18:00", frequency="Daily"))
	mochi.add_task(Task(description="Morning walk", time="07:30", frequency="Daily"))
	mochi.add_task(Task(description="Lunch", time="12:15", frequency="Daily"))
	luna.add_task(Task(description="Brush fur", time="20:15", frequency="Weekly"))
	luna.add_task(Task(description="Breakfast", time="08:00", frequency="Daily"))

	owner.add_pet(mochi)
	owner.add_pet(luna)
	scheduler = Scheduler(owner)

	# Intentionally add two tasks at the same time for Mochi.
	warning_message = scheduler.schedule_task(
		"Mochi",
		Task(description="Breakfast", time="07:30", frequency="Daily"),
	)
	if warning_message:
		print(f"Warning: {warning_message}")

	# Add completion status so status filters have visible output.
	scheduler.mark_task_complete("Mochi", "Dinner")

	return scheduler


def print_schedule(title: str, task_items: list[dict]) -> None:
	print(title)
	print("-" * 40)
	if not task_items:
		print("(no tasks)")
		return

	for item in task_items:
		pet_name = item["pet"]
		task = item["task"]
		status = "Done" if task.completed else "Pending"
		print(f"{task.time} | {pet_name:<5} | {task.description} ({task.frequency}) - {status}")


def print_demo_views(scheduler: Scheduler) -> None:
	print_schedule("All tasks (in insertion order)", scheduler.get_all_tasks())
	print()

	print_schedule("Sorted by time", scheduler.sort_tasks_by_time())
	print()

	print_schedule("Filtered: Mochi + completed", scheduler.filter_tasks(pet_name="Mochi", status="completed"))
	print()

	print_schedule("Filtered: pending only", scheduler.filter_tasks(status="pending"))
	print()

	print_schedule("Filtered: Luna only", scheduler.filter_tasks(pet_name="Luna"))



if __name__ == "__main__":
	scheduler = build_sample_schedule()
	print_demo_views(scheduler)
