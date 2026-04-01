# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

My initial UML design included four main classes:
- `Owner`: stores owner name, available hours, and a list of pets; responsible for adding/removing pets and updating availability.
- `Pet`: stores pet name, species, age, owner reference, and a list of tasks; responsible for managing tasks and returning tasks sorted by priority.
- `Task`: stores title, duration, priority, category, and notes; responsible for serializing itself to a dictionary and validating its own data.
- `Scheduler`: owns an `Owner` and a `Pet`, and holds the built schedule and skipped tasks; responsible for scheduling flow with methods like `build_schedule()`, `prioritize()`, `fits_in_window()`, `explain()`, and `summary()`.

**b. Design changes**

- Did your design change during implementation? Yes 
- If yes, describe at least one change and why you made it.

# Priority enum should support ordering
class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3

# Add validation to Pet initialization
def __post_init__(self):
    if self not in self.owner.pets:
        self.owner.add_pet(self)

# Scheduler needs validation
def __post_init__(self):
    if self.pet not in self.owner.pets:
        raise ValueError("Pet must belong to the specified Owner")
---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?
Considerations are: chronological ordering of tasks, recurring schedules, completion state, overlap conflicts based on task duration.

I prioritized constraints that reduce missed care and confusion for the owner, especially “what is due next” and “can this task fit without overlap? I am considering suggesting to the user what activity to complete based on priority ordering in case of conflict

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes. 

A key tradeoff is using a rule-based scheduler instead of a complex optimization system. This means the app is easier to understand and debug, but it may not produce a globally optimal plan.

- Why is that tradeoff reasonable for this scenario?

n. For this project, that tradeoff is reasonable because clarity matter more than advanced optimization as this is a learning project vs an optimal market trady program
---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?
I used AI for design brainstorming, implementation support, and code review. It was most useful when I asked for concrete improvements tied to my actual classes, like sorting tasks by time, filtering by status, and handling recurring task generation after completion.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.

Enumeration of tasks; I initially thought this should be a list that should be appended by user input but as I read the prompt it was still unclear as to whether I should allow a user to input a list of tasks or have predefined tasks
- How did you evaluate or verify what the AI suggested?

I reread the prompt to have a better understanding of how my program should work
---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

I tested the core behaviors that make the scheduler useful and reliable:
- marking a task complete updates its status correctly;
- adding tasks to a pet updates task count;
- tasks are sorted in chronological order;
- filtering works by pet and by completion status;
- recurrence behavior works (Daily and Weekly tasks spawn the next occurrence after completion; Monthly does not auto-spawn);
- conflict detection works for same start times and overlapping durations;
- conflict warnings include a recommendation based on task priority.

These tests were important because they validate the exact features users depend on in day-to-day planning: seeing tasks in the right order, avoiding schedule collisions, and preserving continuity for recurring care.

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

I am moderately high in confidence because the main scheduling paths are covered by passing unit tests, including sorting, filtering, recurrence, and conflict logic. I am confident in normal usage scenarios and in the overlap/conflict protections.

If I had more time, I would test more edge cases:
- time parsing edge cases (invalid formats, noon/midnight, and mixed 12-hour/24-hour inputs);
- recurrence edge dates (end-of-month behavior such as tasks starting on the 29th-31st);
- duplicate descriptions for the same pet (to ensure mark_task_complete targets the intended task);
- multi-pet heavy schedules with many overlapping tasks;
- timezone/date-boundary scenarios if the app is later expanded beyond local single-day usage.

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

I am most satisfied with the scheduler evolution from a simple task list into a more realistic planning system. In particular, adding overlap-based conflict detection and priority-based recommendations made the app feel more practical, and the recurring-task continuation logic improved usability.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

In another iteration, I would redesign task identification so each task has a unique ID rather than relying mainly on description text. I would also improve UI guidance around conflicts (for example, suggested alternatives and quick reschedule actions), and I would add persistence so data survives app restarts.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

One key takeaway is that AI is most effective when I use it as a collaborator instead of an answer generator. The best results came from giving specific context, validating every suggestion with tests, and iterating in small steps so design decisions stayed aligned with actual system behavior.
