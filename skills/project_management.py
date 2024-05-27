# TeamForgeAI/skills/project_management.py
import streamlit as st
import re
from current_project import CurrentProject # Import CurrentProject

def project_management(query: str = ""):
    """
    A skill for managing project objectives.

    This skill can be used to:
    - Generate a list of objectives based on a given project description.
    - Add new objectives to the project.
    - Mark objectives as complete or incomplete.

    :param query: A string containing a project description or a command for managing objectives.
    :return: A string containing the current list of objectives or a message indicating the result of the command.
    """
    # Access the current project from session state
    current_project = st.session_state.get("current_project", None)

    if current_project is None:
        return "Error: No active project found."

    # If no query is provided, return the current list of objectives and deliverables
    if not query:
        objectives_str = "Objectives:\n"
        for i, obj in enumerate(current_project.objectives):
            objectives_str += f"{i+1}. [{'x' if obj['done'] else ' '}] {obj['text']}\n"

        deliverables_str = "Deliverables:\n"
        for i, deliverable in enumerate(current_project.deliverables):
            deliverables_str += f"{i+1}. [{'x' if deliverable['done'] else ' '}] {deliverable['text']}\n"

        return objectives_str + "\n" + deliverables_str # Return both objectives and deliverables

    # Handle commands for managing objectives and deliverables
    commands = {
        "add objective": lambda obj: current_project.add_objective(obj),
        "done objective": lambda index: current_project.mark_objective_done(int(index) - 1),
        "undone objective": lambda index: current_project.mark_objective_undone(int(index) - 1),
        "add deliverable": lambda obj: current_project.add_deliverable(obj),
        "done deliverable": lambda index: current_project.mark_deliverable_done(int(index) - 1),
        "undone deliverable": lambda index: current_project.mark_deliverable_undone(int(index) - 1),
    }

    # Parse the query to extract the command and argument
    match = re.match(r"(\w+\s+\w+)\s*(.*)", query) # Modified regex to capture two words for command
    if match:
        command, arg = match.groups()
        if command in commands:
            try:
                commands[command](arg)
                st.session_state.current_project = current_project # Update the session state
                st.experimental_rerun() # Trigger a rerun to reflect the changes
                return f"{command} successfully."
            except Exception as e:
                return f"Error: {e}"
        else:
            return f"Error: Invalid command '{command}'."
    else:
        return "Error: Invalid query format."

def update_checklists(discussion_history: str, current_project: CurrentProject):
    """
    Analyzes the discussion history and updates the Objectives and Deliverables lists.
    """
    # Implement logic to identify completed objectives and deliverables
    # For now, let's just check if the objective/deliverable text is present in the discussion history
    for i, obj in enumerate(current_project.objectives):
        if obj["text"] in discussion_history:
            current_project.mark_objective_done(i)

    for i, deliverable in enumerate(current_project.deliverables):
        if deliverable["text"] in discussion_history:
            current_project.mark_deliverable_done(i)
