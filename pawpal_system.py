from __future__ import annotations
"""Core domain models and scheduling helpers for the PawPal app."""

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from typing import Any, Dict, List, Optional


_PRIORITY_RANK = {
    "high": 3,
    "medium": 2,
    "low": 1,
}


def _parse_task_time(value: str) -> time:
    """Parse a task time string into a time object.

    Accepts 24-hour format (HH:MM) and 12-hour format (H:MM AM/PM).
    """
    for fmt in ("%H:%M", "%I:%M %p"):
        try:
            return datetime.strptime(value.strip(), fmt).time()
        except ValueError:
            continue
    raise ValueError("Task time must use HH:MM or H:MM AM/PM format.")


def _task_slot(task: Task) -> tuple[date, time]:
    """Return the schedule slot key used for conflict comparisons."""
    return (task.starts_on, _parse_task_time(task.time))


def _task_interval(task: Task) -> tuple[datetime, datetime]:
    """Return concrete start/end datetimes for one scheduled task instance."""
    start_dt = datetime.combine(task.starts_on, _parse_task_time(task.time))
    end_dt = start_dt + timedelta(minutes=task.duration_minutes)
    return start_dt, end_dt


def _intervals_overlap(first: Task, second: Task) -> bool:
    """Return True when two tasks overlap in time on the same date."""
    if first.starts_on != second.starts_on:
        return False

    first_start, first_end = _task_interval(first)
    second_start, second_end = _task_interval(second)
    return first_start < second_end and second_start < first_end


def _priority_rank(task: Task) -> int:
    """Return numeric priority rank where higher means more important."""
    return _PRIORITY_RANK.get(task.priority.strip().lower(), _PRIORITY_RANK["medium"])


def _recommended_task_for_conflict(first: Task, second: Task) -> Task:
    """Return which task should be completed first in an overlap conflict."""
    return max(
        [first, second],
        key=lambda task: (
            _priority_rank(task),
            -_parse_task_time(task.time).hour,
            -_parse_task_time(task.time).minute,
            -task.duration_minutes,
        ),
    )


def _collect_conflicting_pairs(items: List[Dict[str, Any]]) -> List[tuple[Dict[str, Any], Dict[str, Any]]]:
    """Return first/second task pairs that overlap in scheduled time."""
    conflicts: List[tuple[Dict[str, Any], Dict[str, Any]]] = []

    sorted_items = sorted(
        items,
        key=lambda item: (
            item["task"].starts_on,
            _parse_task_time(item["task"].time),
            item["pet"].lower(),
            item["task"].description.lower(),
        ),
    )

    for index, first_item in enumerate(sorted_items):
        for second_item in sorted_items[index + 1 :]:
            first_day = first_item["task"].starts_on
            second_day = second_item["task"].starts_on

            if second_day > first_day:
                break

            if _intervals_overlap(first_item["task"], second_item["task"]):
                conflicts.append((first_item, second_item))

    return conflicts


@dataclass
class Task:
    """Represents one pet-care activity with schedule and completion state."""

    description: str
    time: str
    frequency: str
    duration_minutes: int = 30
    priority: str = "Medium"
    completed: bool = False
    starts_on: date = field(default_factory=date.today)

    def __post_init__(self) -> None:
        """Run validation after object creation."""
        self.validate()

    def validate(self) -> None:
        """Validate required task fields and time format."""
        if not self.description.strip():
            raise ValueError("Task description cannot be empty.")
        _parse_task_time(self.time)
        if not self.frequency.strip():
            raise ValueError("Task frequency cannot be empty.")
        if self.duration_minutes <= 0:
            raise ValueError("Task duration must be a positive number of minutes.")
        if self.priority.strip().lower() not in _PRIORITY_RANK:
            raise ValueError("Task priority must be High, Medium, or Low.")

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.completed = True

    def mark_incomplete(self) -> None:
        """Reset this task to incomplete status."""
        self.completed = False

    def to_dict(self) -> Dict[str, Any]:
        """Return a dictionary view of the task."""
        return {
            "description": self.description,
            "time": self.time,
            "frequency": self.frequency,
            "duration_minutes": self.duration_minutes,
            "priority": self.priority,
            "completed": self.completed,
            "starts_on": self.starts_on.isoformat(),
        }

    def occurs_on(self, day: date) -> bool:
        """Return whether this recurring task should run on the given date."""
        if day < self.starts_on:
            return False

        frequency = self.frequency.strip().lower()
        if frequency == "daily":
            return True
        if frequency == "weekly":
            return day.weekday() == self.starts_on.weekday()
        if frequency == "monthly":
            return day.day == self.starts_on.day
        return False


@dataclass
class Pet:
    """Stores pet profile data and its list of care tasks."""

    name: str
    species: str
    age: int
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> Optional[str]:
        """Add a task when possible, otherwise return a warning message."""
        conflict_task = self.find_overlapping_task(task)
        if conflict_task is not None:
            recommended_task = _recommended_task_for_conflict(conflict_task, task)
            return (
                f"Task conflict for {self.name}: '{task.description}' at {task.time} "
                f"overlaps with '{conflict_task.description}' ({conflict_task.time}) on "
                f"{task.starts_on.isoformat()}. There is not enough time to complete "
                f"both activities in that time window. "
                f"Recommended activity to complete first: '{recommended_task.description}' "
                f"(Priority: {recommended_task.priority})."
            )
        if task in self.tasks:
            return "Task already exists for this pet."
        self.tasks.append(task)
        return None

    def remove_task(self, task: Task) -> None:
        """Remove a task if it exists in the list."""
        if task in self.tasks:
            self.tasks.remove(task)

    def get_tasks(self) -> List[Task]:
        """Return all tasks for this pet."""
        return list(self.tasks)

    def get_pending_tasks(self) -> List[Task]:
        """Return only tasks not yet completed."""
        return [task for task in self.tasks if not task.completed]

    def get_completed_tasks(self) -> List[Task]:
        """Return only tasks already completed."""
        return [task for task in self.tasks if task.completed]

    def has_time_conflict(self, new_task: Task) -> bool:
        """Return True when a task overlaps with an existing task for this pet."""
        return self.find_overlapping_task(new_task) is not None

    def find_overlapping_task(self, new_task: Task) -> Optional[Task]:
        """Return the first existing task that overlaps in time with the new task."""
        for task in self.tasks:
            if _intervals_overlap(task, new_task):
                return task
        return None

    def get_conflicts(self) -> List[Dict[str, str]]:
        """Return pairs of tasks that conflict by overlapping scheduled windows."""
        items = [{"pet": self.name, "task": task} for task in self.tasks]
        return [
            {
                "time": second["task"].time,
                "date": second["task"].starts_on.isoformat(),
                "first_task": first["task"].description,
                "second_task": second["task"].description,
            }
            for first, second in _collect_conflicting_pairs(items)
        ]


@dataclass
class Owner:
    """Represents a pet owner and the pets under their care."""

    name: str
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet if it is not already linked to this owner."""
        if pet not in self.pets:
            self.pets.append(pet)

    def remove_pet(self, pet: Pet) -> None:
        """Remove a pet if it is currently linked to this owner."""
        if pet in self.pets:
            self.pets.remove(pet)

    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """Return tasks for all pets as pet-task pairs."""
        all_tasks: List[Dict[str, Any]] = []
        for pet in self.pets:
            for task in pet.tasks:
                all_tasks.append({"pet": pet.name, "task": task})
        return all_tasks


@dataclass
class Scheduler:
    """Central task manager that retrieves and organizes tasks across pets."""

    owner: Owner

    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """Return all tasks owned by this scheduler's owner."""
        return self.owner.get_all_tasks()

    def get_tasks_for_pet(self, pet_name: str) -> List[Task]:
        """Return all tasks for one pet by name."""
        pet = self._find_pet(pet_name)
        return pet.get_tasks() if pet else []

    def get_pending_tasks(self) -> List[Dict[str, Any]]:
        """Return only incomplete tasks across all pets."""
        return [item for item in self.get_all_tasks() if not item["task"].completed]

    def get_completed_tasks(self) -> List[Dict[str, Any]]:
        """Return only completed tasks across all pets."""
        return [item for item in self.get_all_tasks() if item["task"].completed]

    def organize_tasks(self, completed_first: bool = False) -> List[Dict[str, Any]]:
        """Sort tasks by completion grouping, then time, pet name, and description."""
        return sorted(
            self.get_all_tasks(),
            key=lambda item: (
                0 if item["task"].completed == completed_first else 1,
                _parse_task_time(item["task"].time),
                item["pet"].lower(),
                item["task"].description.lower(),
            ),
        )

    def sort_tasks_by_time(self) -> List[Dict[str, Any]]:
        """Sort all tasks by time, then pet name and task description."""
        return sorted(
            self.get_all_tasks(),
            key=lambda item: (
                _parse_task_time(item["task"].time),
                item["pet"].lower(),
                item["task"].description.lower(),
            ),
        )

    def filter_tasks(
        self,
        pet_name: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Filter tasks by pet and status where status is 'pending' or 'completed'."""
        filtered = self.get_all_tasks()

        if pet_name:
            target_pet = pet_name.strip().lower()
            filtered = [item for item in filtered if item["pet"].lower() == target_pet]

        if status:
            target_status = status.strip().lower()
            if target_status == "completed":
                filtered = [item for item in filtered if item["task"].completed]
            elif target_status == "pending":
                filtered = [item for item in filtered if not item["task"].completed]

        return filtered

    def get_tasks_for_date(self, day: date) -> List[Dict[str, Any]]:
        """Return all recurring tasks that should occur on the provided date."""
        return [item for item in self.get_all_tasks() if item["task"].occurs_on(day)]

    def detect_conflicts(self) -> List[Dict[str, str]]:
        """Return cross-pet conflicts where tasks overlap in scheduled windows."""
        return [
            {
                "time": second["task"].time,
                "date": second["task"].starts_on.isoformat(),
                "first_pet": first["pet"],
                "first_task": first["task"].description,
                "second_pet": second["pet"],
                "second_task": second["task"].description,
            }
            for first, second in _collect_conflicting_pairs(self.sort_tasks_by_time())
        ]

    def get_tasks_by_frequency(self, frequency: str) -> List[Dict[str, Any]]:
        """Return tasks matching a frequency label, case-insensitively."""
        target_frequency = frequency.strip().lower()
        return [
            item
            for item in self.get_all_tasks()
            if item["task"].frequency.strip().lower() == target_frequency
        ]

    def schedule_task(self, pet_name: str, task: Task) -> Optional[str]:
        """Schedule a task for a pet and return a warning message if not added."""
        pet = self._find_pet(pet_name)
        if pet is None:
            return f"Pet '{pet_name}' was not found."
        return pet.add_task(task)

    def mark_task_complete(self, pet_name: str, description: str) -> bool:
        """Mark a matching task complete and create next daily/weekly occurrence."""
        pet = self._find_pet(pet_name)
        if pet is None:
            return False
        task = self._find_task(pet_name, description)
        if task is None:
            return False

        if task.completed:
            return True

        task.mark_complete()
        self._spawn_next_recurring_task(pet, task)
        return True

    def mark_task_incomplete(self, pet_name: str, description: str) -> bool:
        """Mark a matching task incomplete and return True on success."""
        task = self._find_task(pet_name, description)
        if task is None:
            return False
        task.mark_incomplete()
        return True

    def summary(self) -> Dict[str, int]:
        """Return aggregate counts for pets and task statuses."""
        all_tasks = self.get_all_tasks()
        return {
            "pets": len(self.owner.pets),
            "tasks": len(all_tasks),
            "completed": sum(1 for item in all_tasks if item["task"].completed),
            "pending": sum(1 for item in all_tasks if not item["task"].completed),
        }

    def _find_pet(self, pet_name: str) -> Optional[Pet]:
        """Find a pet by name, case-insensitively."""
        for pet in self.owner.pets:
            if pet.name.lower() == pet_name.strip().lower():
                return pet
        return None

    def _find_task(self, pet_name: str, description: str) -> Optional[Task]:
        """Find a task by pet and description, case-insensitively."""
        pet = self._find_pet(pet_name)
        if pet is None:
            return None
        for task in pet.tasks:
            if task.description.lower() == description.strip().lower():
                return task
        return None

    def _spawn_next_recurring_task(self, pet: Pet, task: Task) -> None:
        """Create the next task instance for daily or weekly recurring tasks."""
        frequency = task.frequency.strip().lower()
        next_starts_on: Optional[date] = None

        if frequency == "daily":
            next_starts_on = task.starts_on + timedelta(days=1)
        elif frequency == "weekly":
            next_starts_on = task.starts_on + timedelta(days=7)

        if next_starts_on is None:
            return

        next_task = Task(
            description=task.description,
            time=task.time,
            frequency=task.frequency,
            starts_on=next_starts_on,
        )
        if not pet.has_time_conflict(next_task):
            pet.add_task(next_task)
