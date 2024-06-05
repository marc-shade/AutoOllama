"""
Skill module for updating project status based on discussion history in TeamForgeAI.
"""

import re
import streamlit as st
from current_project import CurrentProject


def update_project_status(query: str = "", agents_data: list = None) -> None:
    """
    A skill to analyze the discussion history and update the project status UI.

    This skill is controlled by the Project Manager agent.

    :param query: Not used in this skill.
    :param agents_data: Not used in this skill.
    """
    # Access the current project from session state
    current_project = st.session_state.get("current_project", None)

    if current_project is None:
        st.error("Error: No active project found.")
        return

    discussion_history = st.session_state.get("discussion_history", "")

    # Analyze the discussion history and update objectives and deliverables
    update_checklists(discussion_history, current_project)
    st.session_state.current_project = current_project  # Update session state


def update_checklists(discussion_history: str, current_project: CurrentProject) -> None:
    """
    Analyzes the discussion history and updates the Objectives and Deliverables lists
    based on the Project Manager's decisions.

    :param discussion_history: The history of discussions in the project.
    :param current_project: The current project being managed.
    """
    objective_pattern = re.compile(
        r"(?:Objective|objective)\s*(\d+)\s*(?:approved|complete|done|not approved|incomplete|needs work)",
        re.IGNORECASE
    )
    deliverable_pattern = re.compile(
        r"(?:Deliverable|deliverable)\s*(\d+)\s*(?:approved|complete|done|not approved|incomplete|needs work)",
        re.IGNORECASE
    )

    # Split the discussion history into individual lines
    discussion_lines = discussion_history.strip().split("\n")

    # Iterate through the discussion lines in reverse order
    for line in reversed(discussion_lines):
        # Check for objective status updates
        for i, obj in enumerate(current_project.objectives):
            matches = objective_pattern.findall(line)
            for match in matches:
                if int(match) == i + 1:
                    if any(
                        phrase in line for phrase in [
                            f"Objective {i+1} approved", f"Objective {i+1} complete",
                            f"Objective {i+1} done", f"Completed objective {i+1}"
                        ]
                    ):
                        current_project.mark_objective_done(i)
                    elif any(
                        phrase in line for phrase in [
                            f"Objective {i+1} not approved", f"Objective {i+1} incomplete",
                            f"Objective {i+1} needs work"
                        ]
                    ):
                        current_project.mark_objective_undone(i)
                    break  # Stop checking for this objective once a status update is found

        # Check for deliverable status updates
        for i, deliverable in enumerate(current_project.deliverables):
            matches = deliverable_pattern.findall(line)
            for match in matches:
                if int(match) == i + 1:
                    if any(
                        phrase in line for phrase in [
                            f"Deliverable {i+1} approved", f"Deliverable {i+1} complete",
                            f"Deliverable {i+1} done", f"Completed deliverable {i+1}"
                        ]
                    ):
                        current_project.mark_deliverable_done(i)
                    elif any(
                        phrase in line for phrase in [
                            f"Deliverable {i+1} not approved", f"Deliverable {i+1} incomplete",
                            f"Deliverable {i+1} needs work"
                        ]
                    ):
                        current_project.mark_deliverable_undone(i)
                    break  # Stop checking for this deliverable once a status update is found
