# TeamForgeAI/current_project.py
class CurrentProject:
    """
    Represents the current project, storing its re-engineered prompt, objectives, deliverables, and goal.
    """
    def __init__(self):
        """Initializes the CurrentProject object with empty lists for objectives and deliverables."""
        self.re_engineered_prompt = ""
        self.objectives = []
        self.deliverables = []
        self.goal = ""

    def set_re_engineered_prompt(self, prompt: str) -> None:
        """Sets the re-engineered prompt for the current project."""
        self.re_engineered_prompt = prompt

    def add_objective(self, objective: str) -> None:
        """Adds an objective to the current project."""
        self.objectives.append({"text": objective, "done": False})

    def add_deliverable(self, deliverable: str) -> None:
        """Adds a deliverable to the current project."""
        self.deliverables.append({"text": deliverable, "done": False})

    def set_goal(self, goal: str) -> None:
        """Sets the goal for the current project."""
        self.goal = goal

    def mark_objective_done(self, index: int) -> None:
        """Marks an objective at the specified index as done."""
        if 0 <= index < len(self.objectives):
            self.objectives[index]["done"] = True

    def mark_deliverable_done(self, index: int) -> None:
        """Marks a deliverable at the specified index as done."""
        if 0 <= index < len(self.deliverables):
            self.deliverables[index]["done"] = True

    def mark_objective_undone(self, index: int) -> None:
        """Marks an objective at the specified index as not done."""
        if 0 <= index < len(self.objectives):
            self.objectives[index]["done"] = False

    def mark_deliverable_undone(self, index: int) -> None:
        """Marks a deliverable at the specified index as not done."""
        if 0 <= index < len(self.deliverables):
            self.deliverables[index]["done"] = False

    def all_objectives_done(self) -> bool:
        """
        Checks if all objectives are marked as done.

        :return: True if all objectives are done, False otherwise.
        """
        return all(objective["done"] for objective in self.objectives)

    def all_deliverables_done(self) -> bool:
        """
        Checks if all deliverables are marked as done.

        :return: True if all deliverables are done, False otherwise.
        """
        return all(deliverable["done"] for deliverable in self.deliverables)