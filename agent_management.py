import base64
import os
import re
import shutil
import json
import random

import streamlit as st

from api_utils import send_request_to_ollama_api, get_ollama_models
from file_utils import (
    load_skills,
    save_agent_to_json,
    load_agents_from_json,
    emoji_list,
)
from ui.discussion import update_discussion_and_whiteboard
from agent_interactions import process_agent_interaction, generate_and_display_image
from ui.utils import extract_keywords


def agent_button_callback(agent_index):
    """Callback function for when an agent button is clicked."""

    def callback():
        st.session_state["selected_agent_index"] = agent_index
        agent = st.session_state.agents_data[agent_index]
        agent_name = (
            agent["config"]["name"]
            if "config" in agent and "name" in agent["config"]
            else ""
        )
        st.session_state["form_agent_name"] = agent_name
        st.session_state["form_agent_description"] = (
            agent["description"] if "description" in agent else ""
        )

        # --- Get the agent's selected skill ---
        selected_skill = agent.get("skill")

        # --- Execute the skill directly if it's assigned ---
        if selected_skill:
            available_skills = load_skills()
            if selected_skill in available_skills:
                skill_function = available_skills[selected_skill]

                # --- Prepare the query based on the skill ---
                user_input = st.session_state.get("user_input", "")
                rephrased_request = st.session_state.get("rephrased_request", "")
                if selected_skill == "web_search":
                    keywords = extract_keywords(rephrased_request) + extract_keywords(
                        st.session_state.get("discussion_history", "")
                    )
                    query = " ".join(keywords)
                elif selected_skill == "generate_sd_images":
                    query = st.session_state.get("discussion_history", "")
                elif selected_skill == "plot_diagram":
                    query = "{}"
                else:
                    query = user_input

                # --- Execute the skill ---
                skill_result = skill_function(query=query)

                # --- Handle the skill result ---
                if selected_skill == "generate_sd_images":
                    pass
                elif selected_skill == "plot_diagram":
                    if skill_result.startswith("Error:"):
                        st.error(skill_result)
                    else:
                        st.image(skill_result, caption="Generated Diagram")
                else:
                    if isinstance(skill_result, list):
                        formatted_results = "\n".join(
                            [f"- {title}: {url} ({snippet})" for title, url, snippet in skill_result]
                        )
                        response_text = formatted_results
                    else:
                        response_text = f"Skill '{selected_skill}' result: {skill_result}"

                    update_discussion_and_whiteboard(agent_name, response_text, user_input)

        else:
            process_agent_interaction(agent_index)

    return callback


def delete_agent(index):
    """Deletes an agent from the system."""
    if 0 <= index < len(st.session_state.agents_data):
        agent = st.session_state.agents_data[index]
        expert_name = agent["config"]["name"]
        current_team = st.session_state.get("current_team", "agents")
        del st.session_state.agents_data[index]

        agents_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", current_team)
        )
        json_file = os.path.join(agents_dir, f"{expert_name}.json")

        if os.path.exists(json_file):
            os.remove(json_file)
            print(f"JSON file deleted: {json_file}")
        else:
            print(f"JSON file not found: {json_file}")

    st.session_state["trigger_rerun"] = True


def remove_agent_from_ui(index):
    """Removes an agent from the UI."""
    if 0 <= index < len(st.session_state.agents_data):
        del st.session_state.agents_data[index]
    st.session_state["trigger_rerun"] = True


def display_agents():
    """Displays the agents in the sidebar."""
    agents_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "agents"))
    if "current_team" not in st.session_state:
        st.session_state["current_team"] = "agents"

    # Agent Loading and Display
    if "agents_data" not in st.session_state:
        st.session_state["agents_data"] = load_agents_from_json(
            os.path.join("..", st.session_state["current_team"]) + "/"
        )

    if st.session_state.agents_data:
        st.sidebar.title("Your Agents")
        st.sidebar.subheader("Click to interact")

        for index, agent in enumerate(st.session_state.agents_data):
            agent_name = (
                agent["config"]["name"]
                if agent["config"].get("name")
                else f"Unnamed Agent {index + 1}"
            )

            # --- Check if the agent belongs to the currently selected team ---
            agent_file_path = os.path.abspath(
                os.path.join(
                    os.path.dirname(__file__),
                    "..",
                    st.session_state["current_team"],
                    f"{agent_name}.json",
                )
            )
            if os.path.exists(agent_file_path):
                col1, col2, col3, col4 = st.sidebar.columns([1, 1, 1, 5])
                with col1:
                    if st.button("⚙️", key=f"gear_{index}"):
                        st.session_state["edit_agent_index"] = index
                        st.session_state["show_edit"] = True
                        save_agent_to_json(
                            agent,
                            f"{st.session_state.current_team}/{agent['config']['name']}.json",
                        )
                with col2:
                    if st.button("🗑️", key=f"delete_{index}", on_click=lambda i=index: delete_agent(i)):
                        pass
                with col3:
                    if st.button("🚫", key=f"remove_{index}", on_click=lambda i=index: remove_agent_from_ui(i)):
                        pass

                with col4:
                    if "next_agent" in st.session_state and st.session_state.next_agent == agent_name:
                        button_style = """
                        <style>
                        .custom-button {
                            background-color: #f0f0f0;
                            color: black;
                            padding: 0rem .3rem;
                            border: none;
                            border-radius: 0.25rem;
                            cursor: pointer.
                        }
                        .custom-button.active {
                            background-color: green;
                            color: white.
                        }
                        </style>
                        """
                        st.markdown(
                            button_style
                            + f'<button class="custom-button active">{agent.get("emoji", "🐶")} {agent_name}</button>',
                            unsafe_allow_html=True,
                        )
                    else:
                        st.button(
                            f'{agent.get("emoji", "🐶")} {agent_name}',
                            key=f"agent_{index}",
                            on_click=agent_button_callback(index),
                        )

        teams = ["agents"] + [
            f
            for f in os.listdir(agents_dir)
            if os.path.isdir(os.path.join(agents_dir, f))
        ]

        handle_agent_editing(teams)

    else:
        teams = ["agents"] + [
            f
            for f in os.listdir(agents_dir)
            if os.path.isdir(os.path.join(agents_dir, f))
        ]

    # Add Agent Section
    new_agent_role = st.sidebar.text_input("New Agent Role", key="new_agent_role")
    if st.sidebar.button("Add Agent", key="add_agent"):
        new_agent_skills = assign_skills(new_agent_role)  # Assign skills based on role
        new_agent_model = select_model(new_agent_skills)  # Select model based on skills

        new_agent = {
            "type": "assistant",
            "config": {
                "name": new_agent_role,
                "system_message": "You are a helpful assistant.",
            },
            "description": "A new agent.",
            "skill": new_agent_skills,
            "tools": [],
            "ollama_url": "http://localhost:11434",  # Default agent-specific settings
            "temperature": 0.10,
            "model": new_agent_model,
        }
        st.session_state.agents_data.append(new_agent)
        save_agent_to_json(
            new_agent,
            f"{st.session_state.current_team}/{new_agent['config']['name']}.json",
        )
        st.session_state["trigger_rerun"] = True

    # Team Management Section
    st.sidebar.title("Team Management")
    new_team_name = st.sidebar.text_input("New Team Name", key="new_team_name")
    if st.sidebar.button("Create Team", key="create_team"):
        if not os.path.exists(os.path.join(agents_dir, new_team_name)):
            os.makedirs(os.path.join(agents_dir, new_team_name))
            st.session_state["trigger_rerun"] = True
            st.rerun()

    # Team Selection
    selected_team = st.sidebar.selectbox("Select Team", teams, key="selected_agent_team")
    st.session_state["current_team"] = (
        "agents"
        if selected_team == "agents"
        else os.path.join("agents", selected_team)
    )


def assign_skills(role):
    """Assign skills to an agent based on its role."""
    role_to_skills_mapping = {
        "Project Manager": ["project_management"],
        "Storyline Developer": ["generate_sd_images", "plot_diagram"],
        "Illustrator Designer": ["generate_sd_images"],
        "Content Writer": ["fetch_web_content"],
        "Moral Lesson Consultant": ["project_management"],
    }
    return role_to_skills_mapping.get(role, [])


def select_model(skills):
    """Select the appropriate model for the new agent based on assigned skills."""
    available_models = get_ollama_models("http://localhost:11434")
    print(f"Available models: {available_models}")  # Debugging line

    if not available_models:
        return "default_model"  # Fallback model if no models are available

    if skills:
        skill_based_model_mapping = {
            'project_management': 'mistral:7b-instruct-v0.2-q8_0',
            'generate_sd_images': 'llama3:8b',
            'plot_diagram': 'llama3:8b',
            'fetch_web_content': 'mistral:7b-instruct-v0.2-q8_0'
        }
        for skill in skills:
            if skill in skill_based_model_mapping:
                return skill_based_model_mapping[skill]
    return "llama3:8b"  # Default model if no specific skill model is found


def handle_agent_editing(teams):
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
        if edit_index is not None and 0 <= edit_index < len(st.session_state.agents_data):
            agent = st.session_state.agents_data[edit_index]
            with st.expander(f"Edit Properties of {agent['config'].get('name', '')}", expanded=True):
                edit_agent_properties(agent, teams)


def edit_agent_properties(agent, teams):
    """Provides UI elements for editing agent properties."""
    edit_index = st.session_state.get("edit_agent_index")
    new_name = st.text_input("Name", value=agent["config"].get("name", ""), key=f"name_{edit_index}")
    description_value = agent.get("new_description", agent.get("description", ""))
    new_description = st.text_area("Description", value=description_value, key=f"desc_{edit_index}")

    available_skills = load_skills()
    agent_skill = agent.get("skill", None)
    # Correct the index logic to handle strings and None
    skill_index = 0  # Default index
    if isinstance(agent_skill, list) and agent_skill:
        skill_index = ([None] + list(available_skills.keys())).index(agent_skill[0]) if agent_skill[0] in available_skills else 0
    elif isinstance(agent_skill, str) and agent_skill:
        skill_index = ([None] + list(available_skills.keys())).index(agent_skill) if agent_skill in available_skills else 0
    selected_skill = st.selectbox(
        "Skill",
        [None] + list(available_skills.keys()),
        index=skill_index,
        key=f"skill_select_{edit_index}",
    )
    agent["skill"] = selected_skill

    selected_emoji = st.selectbox(
        "Emoji",
        emoji_list,
        index=emoji_list.index(agent.get("emoji", "🐶")),
        key=f"emoji_select_{edit_index}",
    )
    agent["emoji"] = selected_emoji

    agent["ollama_url"] = st.text_input("Endpoint", value=agent.get("ollama_url", "http://localhost:11434"), key=f"endpoint_{edit_index}")
    agent["temperature"] = st.slider("Temperature", min_value=0.0, max_value=1.0, value=agent.get("temperature", 0.10), step=0.01, key=f"temperature_{edit_index}")
    available_models = get_ollama_models(agent.get("ollama_url", st.session_state.get("ollama_url", "http://localhost:11434")))
    agent["model"] = st.selectbox("Model", options=available_models, index=available_models.index(agent.get("model", st.session_state.selected_model)) if agent.get("model") in available_models else 0, key=f"model_{edit_index}")

    if st.button("Regenerate", key=f"regenerate_{edit_index}"):
        new_description = regenerate_agent_description(agent)
        if new_description:
            agent["new_description"] = new_description
            print(f"Description regenerated for {agent['config']['name']}: {new_description}")
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
        save_agent_to_json(agent, f"{st.session_state.current_team}/{new_name}.json")
        if old_name != new_name:
            os.remove(f"{st.session_state.current_team}/{old_name}.json")
        st.session_state["trigger_rerun"] = True
        st.session_state[f"save_clicked_{edit_index}"] = False

    move_to_team = st.selectbox(
        "Move to Team",
        teams,
        index=teams.index(st.session_state.get("current_team", "agents").split("/")[-1]),
        key=f"move_to_team_{edit_index}",
    )
    if st.button("Move Agent", key=f"move_agent_{edit_index}"):
        source_path = os.path.join(st.session_state.current_team, f"{agent['config']['name']}.json")
        destination_team = (
            "agents" if move_to_team == "agents" else os.path.join("agents", move_to_team)
        )
        destination_path = os.path.join(destination_team, f"{agent['config']['name']}.json")
        os.makedirs(os.path.dirname(destination_path), exist_ok=True)
        shutil.move(source_path, destination_path)
        st.session_state["trigger_rerun"] = True
        st.rerun()


def regenerate_agent_description(agent):
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
    objectives = "\n".join([f"- {obj['text']}" for obj in current_project.objectives]) if current_project else ""
    deliverables = "\n".join([f"- {d['text']}" for d in current_project.deliverables]) if current_project else ""
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

        Generate a revised prompt for {agent_name} that defines the agent and it's role in the project in best manner possible to address the current goal. Taking into account all the information provided, only prompt the agent based on its role in the project. 

        Return ONLY the revised agent description, without a title, label, or any additional commentary or narrative. 
        It is imperative that you return ONLY the text of the new agent description. You are redefining a prompt in code, keep it clean and tight.
        No preamble, no narrative, no superfluous commentary whatsoever. Just the agent description, unlabeled, no title, please.
    """

    print(f"regenerate_agent_description called with agent_name: {agent_name}")
    print(f"regenerate_agent_description called with prompt: {prompt}")

    response_generator = send_request_to_ollama_api(agent_name, prompt, agent=agent)

    full_response = ""
    try:
        for response_chunk in response_generator:
            response_text = response_chunk.get("response", "")
            full_response += response_text
    except Exception as e:
        print(f"Error processing response generator: {e}")
        return None

    if full_response:
        return full_response.strip()
    else:
        return None


def download_agent_file(expert_name):
    """Provides a download link for the agent JSON file."""
    formatted_expert_name = re.sub(
        r"[^a-zA-Z0-9\s]", "", expert_name
    )
    formatted_expert_name = (
        formatted_expert_name.lower().replace(" ", "_")
    )

    agents_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "agents"))
    json_file = os.path.join(agents_dir, f"{formatted_expert_name}.json")

    if os.path.exists(json_file):
        with open(json_file, "r") as f:
            file_content = f.read()

        b64_content = base64.b64encode(file_content.encode()).decode()

        href = f'<a href="data:file/json;base64,{b64_content}" download="{formatted_expert_name}.json">Download {formatted_expert_name}.json</a>'
        st.markdown(href, unsafe_allow_html=True)
    else:
        st.error(f"File not found: {json_file}")
