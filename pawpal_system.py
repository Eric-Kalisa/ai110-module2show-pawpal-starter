from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Tuple


class Priority(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class Category(Enum):
    FEEDING = "FEEDING"
    WALK = "WALK"
    MEDS = "MEDS"
    GROOMING = "GROOMING"
    ENRICHMENT = "ENRICHMENT"


@dataclass
class Task:
    title: str
    duration_min: int
    priority: Priority
    category: Category
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "duration_min": self.duration_min,
            "priority": self.priority.name,
            "category": self.category.name,
            "notes": self.notes,
        }

    def validate(self) -> None:
        if not self.title:
            raise ValueError("Task title cannot be empty.")
        if self.duration_min <= 0:
            raise ValueError("Task duration must be greater than zero.")
        if not isinstance(self.priority, Priority):
            raise TypeError("priority must be a Priority enum member.")
        if not isinstance(self.category, Category):
            raise TypeError("category must be a Category enum member.")


@dataclass
class Owner:
    name: str
    available_hrs: List[Tuple[str, str]] = field(default_factory=list)
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        if pet not in self.pets:
            self.pets.append(pet)
            pet.owner = self

    def remove_pet(self, pet: Pet) -> None:
        if pet in self.pets:
            self.pets.remove(pet)
            pet.owner = None

    def set_hours(self, hrs: List[Tuple[str, str]]) -> None:
        self.available_hrs = hrs


@dataclass
class Pet:
    name: str
    species: str
    age: int
    owner: Owner
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        if task not in self.tasks:
            self.tasks.append(task)

    def remove_task(self, task: Task) -> None:
        if task in self.tasks:
            self.tasks.remove(task)

    def get_by_priority(self) -> List[Task]:
        return sorted(self.tasks, key=lambda task: task.priority.value, reverse=True)


@dataclass
class Scheduler:
    owner: Owner
    pet: Pet
    schedule: List[Dict[str, Any]] = field(default_factory=list)
    skipped: List[Task] = field(default_factory=list)

    def build_schedule(self) -> None:
        self.schedule.clear()
        self.skipped.clear()
        # TODO: implement scheduling logic

    def prioritize(self, tasks: List[Task]) -> List[Task]:
        # TODO: implement category-based priority rules
        return sorted(tasks, key=lambda task: task.priority.value, reverse=True)

    def fits_in_window(self, task: Task, current_time: str) -> bool:
        # TODO: implement time-window availability checks
        return False

    def explain(self) -> str:
        return "Scheduler explanation not implemented yet."

    def summary(self) -> Dict[str, Any]:
        return {
            "total_time": sum(item.get("task", Task("", 0, Priority.LOW, Category.FEEDING)).duration_min for item in self.schedule),
            "task_count": len(self.schedule),
            "skipped_count": len(self.skipped),
        }
