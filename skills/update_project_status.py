"""
Skill module for updating project status based on discussion history in TeamForgeAI.
"""

import re
import streamlit as st

from current_project import CurrentProject


def update_project_status(query: str = "", agents_data: list = None, discussion_history: str = "") -> str:
    """
    A skill to analyze the discussion history and update the project status UI.

    This skill is controlled by the Project Manager agent.

    :param query: Not used in this skill.
    :param agents_data: Not used in this skill.
    :param discussion_history: The history of discussions in the project.
    :return: Status message indicating what was updated.
    """

    # Access the current project from session state
    current_project = st.session_state.get("current_project", None)
    if current_project is None:
        st.error("Error: No active project found.")
        return "No active project found."

    # Analyze the discussion history and update objectives and deliverables
    status_message = update_checklists(discussion_history, current_project)
    st.session_state["current_project"] = current_project  # Update session state

    # Provide user feedback in the discussion history
    if status_message != "No updates found in the discussion history.":
        st.session_state.discussion_history += f"Project_Manager_LlamaBook: Skill 'update_project_status' result: {status_message}\n\n===\n\n"
        st.session_state["trigger_rerun"] = True  # Trigger a rerun to display the update
    return status_message


def update_checklists(discussion_history: str, current_project: CurrentProject) -> str:
    """
    Analyzes the discussion history and updates the Objectives and Deliverables lists
    based on the Project Manager's decisions.

    :param discussion_history: The history of discussions in the project.
    :param current_project: The current project being managed.
    :return: Status message indicating what was updated.
    """

    updates = []

    # 1. Intelligent Inference: Infer status from agent discussions (Improved)
    for i, objective in enumerate(current_project.objectives):
        if objective['done']:  # Skip already completed objectives
            continue

        # Look for more specific patterns indicating actual completion
        completion_patterns = [
            rf"\*\*Objective\s*{i+1}:\*\*.*(?:is\s*complete|is\s*done|has\s*been\s*achieved|is\s*finished|is\s*ready)",
            rf"I\s*have\s*(?:completed|finished|done).*\*\*Objective\s*{i+1}:\*\*",
            rf"(?:Completed|Finished|Done).*\*\*Objective\s*{i+1}:\*\*",
        ]
        if any(re.search(pattern, discussion_history, re.IGNORECASE) for pattern in completion_patterns):
            current_project.mark_objective_done(i)
            updates.append(f"Objective {i + 1} ({objective['text']}) marked as done based on discussion.")

    for i, deliverable in enumerate(current_project.deliverables):
        if deliverable['done']:  # Skip already completed deliverables
            continue

        # Look for more specific patterns indicating actual completion or submission
        completion_patterns = [
            rf"\*\*Deliverable\s*{i+1}:\*\*.*(?:is\s*complete|is\s*done|has\s*been\s*submitted|has\s*been\s*provided|is\s*finished|is\s*ready)",
            rf"I\s*have\s*(?:completed|finished|done|submitted|provided).*\*\*Deliverable\s*{i+1}:\*\*",
            rf"(?:Completed|Finished|Done|Submitted|Provided).*\*\*Deliverable\s*{i+1}:\*\*",
            rf"Here's.*\*\*Deliverable\s*{i+1}:\*\*",
        ]
        if any(re.search(pattern, discussion_history, re.IGNORECASE) for pattern in completion_patterns):
            current_project.mark_deliverable_done(i)
            updates.append(f"Deliverable {i + 1} ({deliverable['text']}) marked as done based on discussion.")

    if updates:
        return "Updates applied: " + ", ".join(updates)
    return "No updates found in the discussion history."
