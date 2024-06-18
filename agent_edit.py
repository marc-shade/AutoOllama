# TeamForgeAI/agent_edit.py
import base64
import os
import re
import shutil
import random

import streamlit as st

from api_utils import send_request_to_ollama_api, get_ollama_models
from file_utils import (
    load_skills,
    save_agent_to_json,
    emoji_list,
)
from ui.discussion import update_discussion_and_whiteboard
from agent_interactions import process_agent_interaction, generate_and_display_images
from ui.utils import extract_keywords

# --- Function to sanitize agent names ---


def sanitize_agent_name(agent_name: str) -> str:
    """Sanitizes the agent name by replacing invalid characters with underscores."""
    return re.sub(r"[^a-zA-Z0-9_\s]", "_", agent_name)


def open_edit_agent(index: int) -> None:
    """Opens the agent edit panel."""
    st.session_state["edit_agent_index"] = index
    st.session_state["show_edit"] = True


def assign_skills(role: str) -> list:
    """Assign skills to an agent based on its role."""
    role_to_skills_mapping = {
        "Project Manager": ["generate_agent_instructions", "update_project_status"],
        "Storyline Developer": ["None"],
        "Writer": ["None"],
        "Illustrator Designer": ["generate_sd_images"],
        "Researcher": ["fetch_web_content"],
        "Moral Lesson Consultant": ["None"],
    }
    return role_to_skills_mapping.get(role, [])


def select_model(skills: list) -> str:
    """Select the appropriate model for the new agent based on assigned skills."""
    available_models = get_ollama_models("http://localhost:11434")
    print(f"Available models: {available_models}")  # Debugging line

    if not available_models:
        return "default_model"  # Fallback model if no models are available

    if skills:
        skill_based_model_mapping = {
            "generate_agent_instructions": "mistral:instruct",
            "update_project_status": "mistral:instruct",
            "generate_sd_images": "mistral:instruct",
            "plot_diagram": "mistral:instruct",
            "fetch_web_content": "mistral:instruct",
        }
        for skill in skills:
            if skill in skill_based_model_mapping:
                return skill_based_model_mapping[skill]
    return "llama3:8b"  # Default model if no specific skill model is found


def handle_agent_editing(teams: list, agents_base_dir: str) -> None:
    """Handles the editing of agent properties."""
    edit_index = st.session_state.get("edit_agent_index")
    show_edit = st.session_state.get("show_edit")

    if show_edit and (
        edit_index is None or edit_index >= len(st.session_state.agents_data)
    ):
        print("Stale edit_agent_index detected. Resetting session state.")
        st.session_state["show_edit"] = False
        if "edit_agent_index" in st.session_state:
            del st.session_state["edit_agent_index"]

    if show_edit:
        if edit_index is not None and 0 <= edit_index < len(
            st.session_state.agents_data
        ):
            agent = st.session_state.agents_data[edit_index]
            with st.expander(
                f"Edit Properties of {agent['config'].get('name', '')}", expanded=True
            ):
                edit_agent_properties(agent, teams, agents_base_dir)


def edit_agent_properties(agent: dict, teams: list, agents_base_dir: str) -> None:
    """Provides UI elements for editing agent properties."""
    edit_index = st.session_state.get("edit_agent_index")
    new_name = st.text_input(
        "Name", value=agent["config"].get("name", ""), key=f"name_{edit_index}"
    )
    description_value = agent.get("new_description", agent.get("description", ""))
    new_description = st.text_area(
        "Description", value=description_value, key=f"desc_{edit_index}"
    )

    available_skills = load_skills()
    agent_skill = agent.get("skill", None)
    # Correct the index logic to handle strings and None
    skill_index = 0  # Default index
    if isinstance(agent_skill, list) and agent_skill:
        skill_index = (
            ([None] + list(available_skills.keys())).index(agent_skill[0])
            if agent_skill[0] in available_skills
            else 0
        )
    elif isinstance(agent_skill, str) and agent_skill:
        skill_index = (
            ([None] + list(available_skills.keys())).index(agent_skill)
            if agent_skill in available_skills
            else 0
        )
    selected_skill = st.selectbox(
        "Skill",
        [None] + list(available_skills.keys()),
        index=skill_index,
        key=f"skill_select_{edit_index}",
    )
    agent["skill"] = [selected_skill] if selected_skill is not None else []

    selected_emoji = st.selectbox(
        "Emoji",
        emoji_list,
        index=emoji_list.index(agent.get("emoji", "🐶")),
        key=f"emoji_select_{edit_index}",
    )
    agent["emoji"] = selected_emoji

    agent["ollama_url"] = st.text_input(
        "Endpoint",
        value=agent.get("ollama_url", "http://localhost:11434"),
        key=f"endpoint_{edit_index}",
    )
    agent["temperature"] = st.slider(
        "Temperature",
        min_value=0.0,
        max_value=1.0,
        value=agent.get("temperature", 0.10),
        step=0.01,
        key=f"temperature_{edit_index}",
    )
    available_models = get_ollama_models(
        agent.get("ollama_url", st.session_state.get("ollama_url", "http://localhost:11434"))
    )
    agent["model"] = st.selectbox(
        "Model",
        options=available_models,
        index=available_models.index(
            agent.get("model", st.session_state.selected_model)
        )
        if agent.get("model") in available_models
        else 0,
        key=f"model_{edit_index}",
    )

    # Removed "Database Path" field
    # agent["db_path"] = st.text_input(
    #     "Database Path",
    #     value=agent.get("db_path", f"./db/{agent['config']['name']}"),
    #     key=f"db_path_{edit_index}",
    # )

    agent["enable_memory"] = st.checkbox(
        "Enable Memory",
        value=agent.get("enable_memory", False),
        key=f"enable_memory_{edit_index}",
    )
    agent["enable_moa"] = st.checkbox(
        "Enable MoA",
        value=agent.get("enable_moa", False),
        key=f"enable_moa_{edit_index}",
    )

    if st.button("Regenerate", key=f"regenerate_{edit_index}"):
        new_description = regenerate_agent_description(agent)
        if new_description:
            agent["new_description"] = new_description
            print(
                f"Description regenerated for {agent['config']['name']}: {new_description}"
            )
            st.session_state["trigger_rerun"] = True
        else:
            print(f"Failed to regenerate description for {agent['config']['name']}")

    if f"save_clicked_{edit_index}" not in st.session_state:
        st.session_state[f"save_clicked_{edit_index}"] = False

    if st.button("Save Changes", key=f"save_{edit_index}"):
        st.session_state[f"save_clicked_{edit_index}"] = True

    if st.session_state[f"save_clicked_{edit_index}"]:
        old_name = agent["config"]["name"]
        agent["config"]["name"] = new_name
        agent["description"] = agent.get("new_description", new_description)

        st.session_state["show_edit"] = False
        if "edit_agent_index" in st.session_state:
            del st.session_state["edit_agent_index"]
        if "new_description" in agent:
            del agent["new_description"]
        st.success("Agent properties updated!")
        save_agent_to_json(
            agent,
            os.path.join(
                agents_base_dir, st.session_state["current_team"], f"{new_name}.json"
            ),
        )
        if old_name != new_name:
            os.remove(
                os.path.join(
                    agents_base_dir, st.session_state["current_team"], f"{old_name}.json"
                )
            )
        st.session_state["trigger_rerun"] = True
        st.session_state[f"save_clicked_{edit_index}"] = False

    # Find the index of the current team in the teams list
    current_team_index = teams.index(st.session_state.get("current_team", "agents"))
    move_to_team = st.selectbox(
        "Move to Team",
        teams,
        index=current_team_index,
        key=f"move_to_team_{edit_index}",
    )
    if st.button("Move Agent", key=f"move_agent_{edit_index}"):
        source_path = os.path.join(
            agents_base_dir,
            st.session_state.current_team,
            f"{agent['config']['name']}.json",
        )
        destination_team = move_to_team
        destination_path = os.path.join(
            agents_base_dir, destination_team, f"{agent['config']['name']}.json"
        )
        os.makedirs(os.path.dirname(destination_path), exist_ok=True)
        shutil.move(source_path, destination_path)
        st.session_state["trigger_rerun"] = True  # Trigger a re-run


def regenerate_agent_description(agent: dict) -> str:
    """Regenerates the description for an agent using the LLM."""
    print("Regenerating agent description...")
    print("Session state:", st.session_state)
    agent_name = agent["config"]["name"]
    agent_description = agent["description"]
    user_request = st.session_state.get("user_request", "")
    rephrased_request = st.session_state.get("rephrased_request", "")
    additional_input = st.session_state.get("user_input", "")
    whiteboard = st.session_state.get("whiteboard", "")
    discussion_history = st.session_state.get("discussion_history", "")
    current_project = st.session_state.get("current_project", None)
    objectives = (
        "\n".join([f"- {objective['text']}" for objective in current_project.objectives])
        if current_project
        else ""
    )
    deliverables = (
        "\n".join(
            [f"- {deliverable['text']}" for deliverable in current_project.deliverables]
        )
        if current_project
        else ""
    )
    goal = current_project.goal if current_project else ""

    prompt = f"""
        You are an AI assistant tasked with refining the description of an AI agent named {agent_name}.
        The agent's current description is: {agent_description}

        Consider the following information to refine the agent's description:

        User Request: {user_request}
        Re-engineered Prompt: {rephrased_request}
        Additional Input: {additional_input}
        Whiteboard: {whiteboard}
        Discussion History: {discussion_history}
        Objectives: {objectives}
        Deliverables: {deliverables}
        Goal: {goal}

        Generate a revised prompt for {agent_name} that defines the agent and its role in the project in the best manner possible to address the current goal. Taking into account all the information provided, only prompt the agent based on its role in the project.

        Return ONLY the revised agent description, without a title, label, or any additional commentary or narrative.
        It is imperative that you return ONLY the text of the new agent description. You are redefining a prompt in code, keep it clean and tight.
        No preamble, no narrative, no superfluous commentary whatsoever. Just the agent description, unlabeled, no title, please.
    """

    print(f"regenerate_agent_description called with agent_name: {agent_name}")
    print(f"regenerate_agent_description called with prompt: {prompt}")

    response_generator = send_request_to_ollama_api(agent_name, prompt, agent_data=agent)  # Pass agent_data

    full_response = ""
    try:
        for response_chunk in response_generator:
            response_text = response_chunk.get("response", "")
            full_response += response_text
    except Exception as error:
        print(f"Error processing response generator: {error}")
        return None

    if full_response:
        return full_response.strip()
    return None


def download_agent_file(expert_name: str) -> None:
    """Provides a download link for the agent JSON file."""
    formatted_expert_name = (
        re.sub(r"[^a-zA-Z0-9\s]", "", expert_name).lower().replace(" ", "_")
    )
    agents_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "files", "agents") # Corrected path
    )
    json_file = os.path.join(agents_dir, f"{formatted_expert_name}.json")

    if os.path.exists(json_file):
        with open(json_file, "r", encoding="utf-8") as file:
            file_content = file.read()

        base64_content = base64.b64encode(file_content.encode()).decode()

        href = f'<a href="data:file/json;base64,{base64_content}" download="{formatted_expert_name}.json">Download {formatted_expert_name}.json</a>'
        st.markdown(href, unsafe_allow_html=True)
    else:
        st.error(f"File not found: {json_file}")


def delete_agent(index: int) -> None:
    """Deletes an agent from the system."""
    agents_base_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "TeamForgeAI", "files", "agents") # Corrected path
    )
    if 0 <= index < len(st.session_state.agents_data):
        agent = st.session_state.agents_data[index]
        expert_name = agent["config"]["name"]
        current_team = st.session_state.get("current_team", "agents")
        del st.session_state.agents_data[index]

        # Construct the absolute path to the agent file
        json_file = os.path.join(agents_base_dir, current_team, f"{expert_name}.json")

        # Delete the agent file
        if os.path.exists(json_file):
            os.remove(json_file)
            print(f"JSON file deleted: {json_file}")
        else:
            print(f"JSON file not found: {json_file}")

        st.session_state["trigger_rerun"] = True  # Trigger a re-run


def remove_agent_from_ui(index: int) -> None:
    """Removes an agent from the UI."""
    if 0 <= index < len(st.session_state.agents_data):
        del st.session_state.agents_data[index]
    st.session_state["trigger_rerun"] = True  # Trigger a re-run
