# TeamForgeAI/skills/generate_agent_instructions.py
import streamlit as st
import re
from current_project import CurrentProject # Import CurrentProject

def generate_agent_instructions(query: str = "", agents_data: list = None):
    """
    A skill to generate instructions for other agents based on the current project status.

    This skill is controlled by the Project Manager agent.

    :param query: Not used in this skill.
    :param agents_data: A list of agent data dictionaries.
    :return: A string containing prioritized instructions for other agents.
    """
    # Access the current project from session state
    current_project = st.session_state.get("current_project", None)

    if current_project is None:
        return "Error: No active project found."

    # Generate prioritized instructions for other agents
    instructions = generate_instructions(current_project, agents_data)
    return instructions

def generate_instructions(current_project: CurrentProject, agents_data: list = None) -> str:
    """Generates prioritized instructions for other agents based on the current project status."""
    instructions = "## Prioritized Instructions for Agents:\n\n"

    # Prioritize incomplete objectives
    incomplete_objectives = [obj for obj in current_project.objectives if not obj["done"]]
    if incomplete_objectives:
        instructions += "**Focus on these objectives first:**\n"
        for i, obj in enumerate(incomplete_objectives):
            instructions += f"{i+1}. {obj['text']}\n"
            # Assign the objective to an agent based on skills or role
            agent_name = assign_objective_to_agent(obj['text'], agents_data)
            if agent_name:
                instructions += f"   - Assigned to: **{agent_name}**\n"
        instructions += "\n"

    # If all objectives are done, focus on incomplete deliverables
    elif not current_project.all_objectives_done():
        instructions += "**All objectives are complete. Now focus on these deliverables:**\n"
        for i, deliverable in enumerate(current_project.deliverables):
            if not deliverable["done"]:
                instructions += f"{i+1}. {deliverable['text']}\n"
                # Assign the deliverable to an agent
                agent_name = assign_deliverable_to_agent(deliverable['text'], agents_data)
                if agent_name:
                    instructions += f"   - Assigned to: **{agent_name}**\n"
        instructions += "\n"

    # If all objectives and deliverables are done, the project is complete
    else:
        instructions += "**Congratulations! All objectives and deliverables are complete.**\n"

    return instructions

def assign_objective_to_agent(objective: str, agents_data: list) -> str:
    """Assigns an objective to an agent based on skills or role, excluding the Project Manager."""
    if agents_data is not None:
        for agent in agents_data:
            if agent["config"]["name"] == "Project_Manager":
                continue
            # Simplified agent role detection based on name keywords
            if "Story" in agent["config"]["name"] and any(keyword in objective.lower() for keyword in ["story", "write", "text", "narrative"]):
                return agent["config"]["name"]
            if "Illustrator" in agent["config"]["name"] and any(keyword in objective.lower() for keyword in ["illustrate", "design", "visual", "image"]):
                return agent["config"]["name"]
    return None

def assign_deliverable_to_agent(deliverable: str, agents_data: list) -> str:
    """Assigns a deliverable to an agent based on skills or role."""
    if agents_data is not None:
        for agent in agents_data:
            if agent["config"]["name"] == "Project_Manager":
                continue
            # Simplified agent role detection based on name keywords
            if "Story" in agent["config"]["name"] and any(keyword in deliverable.lower() for keyword in ["story", "write", "text", "narrative"]):
                return agent["config"]["name"]
            if "Illustrator" in agent["config"]["name"] and any(keyword in deliverable.lower() for keyword in ["illustrate", "design", "visual", "image"]):
                return agent["config"]["name"]
    return None