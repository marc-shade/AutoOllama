# TeamForgeAI/skills/summarize_project_status.py
import streamlit as st
from current_project import CurrentProject
import re

def summarize_project_status(query: str = "", agents_data: list = None, discussion_history: str = "") -> str:
    """
    Summarizes the discussion and explicitly states the status of objectives and deliverables.

    This skill can be assigned to the Project Manager or a dedicated Summarizer agent.

    :param query: Not used in this skill.
    :param agents_data: Not used in this skill.
    :param discussion_history: The history of the discussion.
    :return: A structured summary of the project status.
    """

    current_project = st.session_state.get("current_project", None)
    if current_project is None:
        return "Error: No active project found."

    summary = "## Project Status Summary:\n\n"

    summary += "**Discussion Highlights:**\n"
    # Add a brief summary of the key points from the discussion history here (optional)
    # You can use text summarization techniques or simply extract the most recent few lines

    # Update the current_project object based on the discussion history
    update_message = update_checklists(discussion_history, current_project)
    if update_message != "No updates found in the discussion history.":
        summary += f"**Project Management Update:** {update_message}\n\n"

    summary += "\n**Objectives:**\n"
    for i, objective in enumerate(current_project.objectives):
        status = "Completed" if objective["done"] else "In Progress"
        summary += f"**Objective {i+1}:** {objective['text']} - **Status:** {status}\n"

    summary += "\n**Deliverables:**\n"
    for i, deliverable in enumerate(current_project.deliverables):
        status = "Completed" if deliverable["done"] else "In Progress"
        summary += f"**Deliverable {i+1}:** {deliverable['text']} - **Status:** {status}\n"

    return summary

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

        # Look for broader patterns indicating completion
        completion_patterns = [
            rf"\*\*Objective {i+1}:\*\*.*(?:complete|done|finished|achieved|addressed|ready)",
            rf"I\s*have\s*(?:complete|done|finished).*\*\*Objective {i+1}:\*\*",
            rf"\*\*Objective {i+1}:\*\*.*(?:is\s*complete|is\s*done|is\s*finished|has\s*been\s*achieved|looks\s*good|sounds\s*great|we've\s*got\s*that\s*covered)",
            rf"(?:great\s*job|well\s*done|nice\s*work).*\*\*Objective {i+1}:\*\*",
        ]
        if any(re.search(pattern, discussion_history, re.IGNORECASE) for pattern in completion_patterns):
            current_project.mark_objective_done(i)
            updates.append(f"Objective {i + 1} ({objective['text']}) marked as done based on discussion.")

    for i, deliverable in enumerate(current_project.deliverables):
        if deliverable['done']:  # Skip already completed deliverables
            continue

        # Look for broader patterns indicating completion
        completion_patterns = [
            rf"\*\*Deliverable {i+1}:\*\*.*(?:complete|done|finished|submitted|provided|ready)",
            rf"I\s*have\s*(?:complete|done|finished|submitted|provided).*\*\*Deliverable {i+1}:\*\*",
            rf"\*\*Deliverable {i+1}:\*\*.*(?:is\s*complete|is\s*done|is\s*finished|has\s*been\s*submitted|has\s*been\s*provided)",
            rf"(?:here's|i've\s*created|i've\s*finished).*\*\*Deliverable {i+1}:\*\*",
        ]
        if any(re.search(pattern, discussion_history, re.IGNORECASE) for pattern in completion_patterns):
            current_project.mark_deliverable_done(i)
            updates.append(f"Deliverable {i + 1} ({deliverable['text']}) marked as done based on discussion.")

    if updates:
        return "Updates applied: " + ", ".join(updates)
    return "No updates found in the discussion history."
