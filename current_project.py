# TeamForgeAI/current_project.py
class CurrentProject:
    def __init__(self):
        self.re_engineered_prompt = ""
        self.objectives = []
        self.deliverables = []
        self.goal = ""

    def set_re_engineered_prompt(self, prompt):
        self.re_engineered_prompt = prompt

    def add_objective(self, objective):
        self.objectives.append({"text": objective, "done": False})

    def add_deliverable(self, deliverable):
        self.deliverables.append({"text": deliverable, "done": False})

    def set_goal(self, goal):
        self.goal = goal

    def mark_objective_done(self, index):
        if 0 <= index < len(self.objectives):
            self.objectives[index]["done"] = True

    def mark_deliverable_done(self, index):
        if 0 <= index < len(self.deliverables):
            self.deliverables[index]["done"] = True

    def mark_objective_undone(self, index):
        if 0 <= index < len(self.objectives):
            self.objectives[index]["done"] = False

    def mark_deliverable_undone(self, index):
        if 0 <= index < len(self.deliverables):
            self.deliverables[index]["done"] = False
