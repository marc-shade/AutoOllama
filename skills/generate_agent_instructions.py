# TeamForgeAI/generate_agent_instructions.py
import streamlit as st
import re
from current_project import CurrentProject # Import CurrentProject

def generate_agent_instructions(query: str = "", agents_data: list = None, discussion_history: str = "") -> str:
    """
    A skill to generate instructions for other agents based on the current project status.

    This skill is controlled by the Project Manager agent.

    :param query: Not used in this skill.
    :param agents_data: A list of agent data dictionaries.
    :param discussion_history: The history of the discussion.
    :return: A string containing prioritized instructions for other agents.
    """
    # Access the current project from session state
    current_project = st.session_state.get("current_project", None)

    if current_project is None:
        return "Error: No active project found."

    # Initialize the assignment records if they don't exist
    if "objective_assignments" not in st.session_state:
        st.session_state["objective_assignments"] = {}
    if "deliverable_assignments" not in st.session_state:
        st.session_state["deliverable_assignments"] = {}

    # Generate prioritized instructions for other agents
    instructions = generate_instructions(current_project, agents_data, discussion_history)
    return instructions

def generate_instructions(current_project: CurrentProject, agents_data: list = None, discussion_history: str = "") -> str:
    """Generates prioritized instructions for other agents based on the current project status."""
    instructions = "## Prioritized Instructions for Agents:\n\n"

    # Assign objectives
    instructions += "**Objectives:**\n"
    for i, obj in enumerate(current_project.objectives):
        if obj["done"]:  # Skip completed objectives
            continue
        if i not in st.session_state["objective_assignments"]:
            agent_name = assign_objective_to_agent(obj['text'], agents_data)
            if agent_name:
                instructions += generate_objective_prompt(i + 1, obj['text'], agent_name, current_project)
                st.session_state["objective_assignments"][i] = agent_name
        else:
            agent_name = st.session_state["objective_assignments"][i]
            instructions += f"**Objective {i+1}:** {obj['text']} - **Status:** In Progress\n"
            instructions += f"   - **Assigned to:** {agent_name}\n"
    instructions += "\n"

    # Assign deliverables
    if current_project.all_objectives_done():
        instructions += "**Deliverables:**\n"
        for i, deliverable in enumerate(current_project.deliverables):
            if deliverable["done"]:  # Skip completed deliverables
                continue
            if i not in st.session_state["deliverable_assignments"]:
                agent_name = assign_deliverable_to_agent(deliverable['text'], agents_data)
                if agent_name:
                    instructions += generate_deliverable_prompt(i + 1, deliverable['text'], agent_name, current_project)
                    st.session_state["deliverable_assignments"][i] = agent_name
            else:
                agent_name = st.session_state["deliverable_assignments"][i]
                instructions += f"**Deliverable {i+1}:** {deliverable['text']} - **Status:** In Progress\n"
                instructions += f"   - **Assigned to:** {agent_name}\n"
        instructions += "\n"

    # If all objectives and deliverables are done, the project is complete
    if current_project.all_objectives_done() and current_project.all_deliverables_done():
        instructions += "**Congratulations! All objectives and deliverables are complete.**\n"

    return instructions

def objective_already_assigned(objective: str, discussion_history: str) -> bool:
    """Checks if an objective has already been assigned in the discussion history, considering order."""
    pattern = re.compile(rf"\*\*Objective\s*\d+:\*\*\s*{re.escape(objective)}(?:.*?Assigned to: \*\*(.*?)\*\*)?", re.DOTALL)
    match = pattern.search(discussion_history)
    if match:
        assigned_agent = match.group(1)
        if assigned_agent:  # If an agent is assigned, check if the assignment is after the objective text
            objective_start = match.start()
            assigned_start = match.start(1)
            return assigned_start > objective_start
    return False  # No assignment found or assignment is before the objective text

def deliverable_already_assigned(deliverable: str, discussion_history: str) -> bool:
    """Checks if a deliverable has already been assigned in the discussion history, considering order."""
    pattern = re.compile(rf"\*\*Deliverable\s*\d+:\*\*\s*{re.escape(deliverable)}(?:.*?Assigned to: \*\*(.*?)\*\*)?", re.DOTALL)
    match = pattern.search(discussion_history)
    if match:
        assigned_agent = match.group(1)
        if assigned_agent:  # If an agent is assigned, check if the assignment is after the deliverable text
            deliverable_start = match.start()
            assigned_start = match.start(1)
            return assigned_start > deliverable_start
    return False  # No assignment found or assignment is before the deliverable text

def assign_objective_to_agent(objective: str, agents_data: list) -> str:
    """Assigns an objective to an agent based on skills or role, excluding the Project Manager."""
    if agents_data is not None:
        # Find the Project Manager agent
        project_manager = next((agent for agent in agents_data if "Project_Manager" in agent["config"]["name"]), None)
        if project_manager is None:
            return None  # No Project Manager found

        for agent in agents_data:
            if agent == project_manager:  # Skip the Project Manager
                continue
            # Simplified agent role detection based on name keywords
            if "Story" in agent["config"]["name"] and any(keyword in objective.lower() for keyword in ["story", "write", "text", "narrative"]):
                return agent["config"]["name"]
            if "Illustrator" in agent["config"]["name"] and any(keyword in objective.lower() for keyword in ["illustrate", "design", "visual", "image"]):
                return agent["config"]["name"]
            if "Editor" in agent["config"]["name"] and any(keyword in objective.lower() for keyword in ["edit", "revise", "grammar", "spelling", "flow"]):
                return agent["config"]["name"]
    return None

def assign_deliverable_to_agent(deliverable: str, agents_data: list) -> str:
    """Assigns a deliverable to an agent based on skills or role."""
    if agents_data is not None:
        # Find the Project Manager agent
        project_manager = next((agent for agent in agents_data if "Project_Manager" in agent["config"]["name"]), None)
        if project_manager is None:
            return None  # No Project Manager found

        for agent in agents_data:
            if agent == project_manager:  # Skip the Project Manager
                continue
            # Simplified agent role detection based on name keywords
            if "Story" in agent["config"]["name"] and any(keyword in deliverable.lower() for keyword in ["story", "write", "text", "narrative"]):
                return agent["config"]["name"]
            if "Illustrator" in agent["config"]["name"] and any(keyword in deliverable.lower() for keyword in ["illustrate", "design", "visual", "image"]):
                return agent["config"]["name"]
            if "Editor" in agent["config"]["name"] and any(keyword in deliverable.lower() for keyword in ["edit", "revise", "grammar", "spelling", "flow"]):
                return agent["config"]["name"]
    return None

def generate_objective_prompt(objective_number: int, objective_text: str, agent_name: str, current_project: CurrentProject) -> str:
    """Generates a task-specific prompt for an objective."""
    prompt = f"""{agent_name}, you are assigned to **Objective {objective_number}:** {objective_text}\n\n"""

    if "Storyline" in agent_name:
        prompt += f"""The project goal is: {current_project.goal}

Please create a captivating and engaging storyline that fulfills this objective. Consider the target audience and incorporate relevant themes and messages. Provide a detailed outline of the story, including:

* **Title:** A creative and engaging title for the children's book.
* **Logline:** A concise summary of the story's plot.
* **Characters:** Introduce the main character and any supporting characters.
* **Setting:** Describe the world where the story takes place.
* **Plot:** Outline the key events of the story, including the beginning, rising action, climax, falling action, and resolution.
* **Themes:** Highlight the themes and messages you plan to incorporate.
* **Images:** Ask the Illustrator agent to create all the images needed for the project, incorporating all the visual elements needed to tell the story or relay the concept.

Remember to use clear and descriptive language, and ensure the storyline is age-appropriate and engaging for young readers.
"""
    elif "Illustration" in agent_name:
        prompt += f"""The project goal is: {current_project.goal}

Please design visually appealing illustrations that bring the character and story to life. Consider the target audience and create illustrations that are:

* **Engaging and Eye-Catching:** Use bright colors, interesting compositions, and expressive characters to capture the attention of young readers.
* **Age-Appropriate:** Ensure the illustrations are suitable for the target age group.
* **Complementary to the Story:** The illustrations should enhance the narrative and help readers visualize the story's world and characters.

Provide a description of your proposed illustration style, color palette, and any initial sketches or concepts.
"""
    elif "Editor" in agent_name:
        prompt += f"""The project goal is: {current_project.goal}

Please ensure the story flows smoothly from beginning to end. Review the storyline and illustrations for consistency and coherence. Provide feedback and suggestions to improve the overall flow and ensure the story is engaging and easy to follow.

Consider the following:

* **Pacing:** Is the story moving at an appropriate pace?
* **Transitions:** Are the transitions between scenes and chapters smooth and logical?
* **Clarity:** Is the story easy to understand?
* **Engagement:** Is the story captivating and interesting for the target audience?
* **Images:** Ask the Illustrator agent to create all the images needed for the project, incorporating all the visual elements needed to tell the story or relay the concept.

Provide a detailed critique of the storyline and illustrations, highlighting any areas that need improvement.
"""
    else:
        prompt += "Please provide a detailed plan on how you will achieve this objective, including specific steps and expected outcomes."

    return prompt

def generate_deliverable_prompt(deliverable_number: int, deliverable_text: str, agent_name: str, current_project: CurrentProject) -> str:
    """Generates a task-specific prompt for a deliverable."""
    prompt = f"""{agent_name}, you are assigned to **Deliverable {deliverable_number}:** {deliverable_text}\n\n"""

    if "Storyline" in agent_name:
        prompt += f"""The project goal is: {current_project.goal}

Please provide a complete draft of the children's book, including the storyline, illustrations, and text. Ensure that the draft is:

* **Engaging and Age-Appropriate:** The story should be captivating and suitable for the target audience.
* **Well-Structured:** The story should have a clear beginning, middle, and end.
* **Visually Appealing:** The illustrations should complement the text and enhance the reader's experience.
* **Images:** Ask the Illustrator agent to create all the images needed for the project, incorporating all the visual elements needed to tell the story or relay the concept.

Remember to incorporate the relevant objectives and themes into the draft.
"""
    elif "Illustration" in agent_name:
        prompt += f"""The project goal is: {current_project.goal}

Please provide the completed illustrations for the children's book. Ensure that the illustrations are:

* **High-Quality:** The illustrations should be high-resolution and suitable for printing and digital publication.
* **Engaging and Eye-Catching:** Use bright colors, interesting compositions, and expressive characters to capture the attention of young readers.
* **Age-Appropriate:** Ensure the illustrations are suitable for the target age group.
* **Complementary to the Story:** The illustrations should enhance the narrative and help readers visualize the story's world and characters.
"""
    elif "Editor" in agent_name:
        prompt += f"""The project goal is: {current_project.goal}

Please provide the proofread and edited manuscript, ensuring that it is free from grammatical errors, typos, and inconsistencies. The manuscript should also flow smoothly and be engaging for the target audience.

Consider the following:

* **Grammar and Spelling:** Check for any errors in grammar, spelling, punctuation, and capitalization.
* **Clarity and Conciseness:** Ensure the text is clear, concise, and easy to understand.
* **Flow and Coherence:** Evaluate the overall flow of the story, ensuring that the narrative is engaging and easy to follow.
* **Consistency:** Check for consistency in terms of characterization, plot, and tone.
* **Images:** Ask the Illustrator agent to create all the images needed for the project, incorporating all the visual elements needed to tell the story or relay the concept.

Provide the edited manuscript with all corrections and suggestions clearly marked.
"""
    else:
        prompt += "Please provide the completed deliverable, taking into account the project goal and the relevant objectives."

    return prompt
