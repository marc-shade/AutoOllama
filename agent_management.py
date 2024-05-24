# TeamForgeAI/agent_management.py
import base64
import os
import re
import shutil

import streamlit as st

from api_utils import send_request_to_ollama_api
from file_utils import (
    load_skills,
    save_agent_to_json,
    load_agents_from_json,
    emoji_list, # Import the emoji_list
)
from ui.discussion import update_discussion_and_whiteboard
from agent_interactions import process_agent_interaction, generate_and_display_image # Import generate_and_display_image
from ui.utils import extract_keywords # Import extract_keywords here


def agent_button_callback(agent_index):
    """Callback function for when an agent button is clicked."""

    def callback():
        st.session_state["selected_agent_index"] = agent_index
        agent = st.session_state.agents_data[agent_index] # Use agents_data
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
                    keywords = extract_keywords(rephrased_request) + extract_keywords(st.session_state.get("discussion_history", ""))
                    query = " ".join(keywords)
                elif selected_skill == "generate_sd_images":
                    query = st.session_state.get("discussion_history", "")
                else:
                    query = user_input

                # --- Execute the skill ---
                skill_result = skill_function(query=query)

                # --- Handle the skill result ---
                if selected_skill == "generate_sd_images":
                    # Image generation is handled directly by the skill function
                    pass 
                else:
                    if isinstance(skill_result, list):
                        formatted_results = "\n".join(
                            [f"- {title}: {url} ({snippet})" for title, url, snippet in skill_result]
                        )
                        response_text = formatted_results
                    else:
                        response_text = f"Skill '{selected_skill}' result: {skill_result}"

                    update_discussion_and_whiteboard(agent_name, response_text, user_input)

        # --- If no skill is assigned, proceed with regular agent interaction ---
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

    # Team Management Section
    st.sidebar.title("Team Management")
    new_team_name = st.sidebar.text_input("New Team Name", key="new_team_name")
    if st.sidebar.button("Create Team", key="create_team"):
        if not os.path.exists(os.path.join(agents_dir, new_team_name)):
            os.makedirs(os.path.join(agents_dir, new_team_name))
            st.session_state["trigger_rerun"] = True
            st.rerun()

    # Team Selection
    teams = ["agents"] + [
        f
        for f in os.listdir(agents_dir)
        if os.path.isdir(os.path.join(agents_dir, f))
    ]
    selected_team = st.sidebar.selectbox(
        "Select Team", teams, key="selected_agent_team"
    )
    st.session_state["current_team"] = (
        "agents"
        if selected_team == "agents"
        else os.path.join("agents", selected_team)
    )

    # Agent Loading and Display
    if "agents_data" not in st.session_state:
        st.session_state["agents_data"] = load_agents_from_json(
            os.path.join("..", st.session_state["current_team"]) + "/"
        )

    if st.session_state.agents_data: # Updated to use agents_data from session state
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
                os.path.join(os.path.dirname(__file__), "..", st.session_state["current_team"], f"{agent_name}.json")
            )
            if os.path.exists(agent_file_path):
                col1, col2, col3, col4 = st.sidebar.columns([1, 1, 1, 5]) # Removed the 5th column
                with col1:
                    if st.button("⚙️", key=f"gear_{index}"):
                        st.session_state["edit_agent_index"] = index
                        st.session_state["show_edit"] = True
                        save_agent_to_json(
                            agent,
                            f"{st.session_state.current_team}/{agent['config']['name']}.json",
                        )
                with col2:
                    if st.button("🗑️", key=f"delete_{index}", on_click=lambda i=index: delete_agent(i)): # Corrected functionality
                        pass # Placeholder for the on_click event
                with col3:
                    if st.button("🚫", key=f"remove_{index}", on_click=lambda i=index: remove_agent_from_ui(i)): # Corrected functionality
                        pass # Placeholder for the on_click event

                with col4:
                    if (
                        "next_agent" in st.session_state
                        and st.session_state.next_agent == agent_name
                    ):
                        button_style = """
                        <style>
                        .custom-button {
                            background-color: #f0f0f0;
                            color: black;
                            padding: 0rem .3rem;
                            border: none;
                            border-radius: 0.25rem;
                            cursor: pointer;
                        }
                        .custom-button.active {
                            background-color: green;
                            color: white;
                        }
                        </style>
                        """
                        st.markdown(
                            button_style
                            + f'<button class="custom-button active">{agent.get("emoji", "🐶")} {agent_name}</button>', # Add emoji to button text
                            unsafe_allow_html=True,
                        )
                    else:
                        st.button(
                            f'{agent.get("emoji", "🐶")} {agent_name}', # Add emoji to button text
                            key=f"agent_{index}",
                            on_click=agent_button_callback(index),
                        )
                # Removed the Skill Selection from here

        handle_agent_editing(teams)

    # Add Agent Section
    if st.sidebar.button("Add Agent", key="add_agent"):
        new_agent = {
            "type": "assistant",
            "config": {
                "name": "New Agent",
                "system_message": "You are a helpful assistant.",
            },
            "description": "A new agent.",
            "skill": None,
            "tools": [],
        }
        st.session_state.agents_data.append(new_agent) # Correctly append to agents_data
        save_agent_to_json(
            new_agent,
            f"{st.session_state.current_team}/{new_agent['config']['name']}.json",
        )
        st.session_state["trigger_rerun"] = True


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
        if edit_index is not None and 0 <= edit_index < len(
            st.session_state.agents_data # Corrected line
        ):
            agent = st.session_state.agents_data[edit_index] # Corrected line
            with st.expander(
                f"Edit Properties of {agent['config'].get('name', '')}",
                expanded=True,
            ):
                edit_agent_properties(agent, teams)


def edit_agent_properties(agent, teams):
    """Provides UI elements for editing agent properties."""
    edit_index = st.session_state.get("edit_agent_index")
    new_name = st.text_input(
        "Name", value=agent["config"].get("name", ""), key=f"name_{edit_index}"
    )
    description_value = agent.get("new_description", agent.get("description", ""))
    new_description = st.text_area(
        "Description", value=description_value, key=f"desc_{edit_index}"
    )

    # --- Moved Skill Selection to here ---
    available_skills = load_skills()
    agent_skill = agent.get("skill", None)
    selected_skill = st.selectbox(
        "Skill",
        [None] + list(available_skills.keys()),
        index=([None] + list(available_skills.keys())).index(agent_skill) if agent_skill is not None else 0,
        key=f"skill_select_{edit_index}",
    )
    agent["skill"] = selected_skill

    # Emoji Selection
    selected_emoji = st.selectbox(
        "Emoji",
        emoji_list,
        index=emoji_list.index(agent.get("emoji", "🐶")), # Default to dog emoji
        key=f"emoji_select_{edit_index}",
    )
    agent["emoji"] = selected_emoji # Update agent emoji

    if st.button(" Regenerate", key=f"regenerate_{edit_index}"):
        new_description = regenerate_agent_description(agent)
        if new_description:
            agent["new_description"] = new_description
            print(
                f"Description regenerated for {agent['config']['name']}: {new_description}"
            )
            st.session_state["trigger_rerun"] = True
        else:
            print(
                f"Failed to regenerate description for {agent['config']['name']}"
            )

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
            agent, f"{st.session_state.current_team}/{new_name}.json"
        )
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
        source_path = os.path.join(
            st.session_state.current_team, f"{agent['config']['name']}.json"
        )
        destination_team = (
            "agents" if move_to_team == "agents" else os.path.join("agents", move_to_team)
        )
        destination_path = os.path.join(
            destination_team, f"{agent['config']['name']}.json"
        )
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
    discussion_history = st.session_state.get("discussion_history", "")

    prompt = f"""
        You are an AI assistant tasked with refining the description of an AI agent. Below are the agent's current details:
        {agent_name}
        {agent_description}

        Generate a revised description for {agent_name} that defines the agent in the best manner possible to address the current user request, taking into account the discussion thus far. 
            
        Use a step-by-step reasoning process to:
        1. Analyze: {user_request}
        2. Consider the discussion so far for context: {discussion_history}
        2. Identify key areas where this can be improved to better meet the user request: {agent_description}
        3. Generate a revised agent_description that incorporates these improvements.

        Return only the revised agent_description, without a title or any additional commentary or narrative.  It is imperative that you return ONLY the text of the new agent_description.  
        No preamble, no narrative, no superfluous commentary whatsoever.  Just the agent_description, unlabeled, no title, please.
    """

    print(f"regenerate_agent_description called with agent_name: {agent_name}")
    print(f"regenerate_agent_description called with prompt: {prompt}")

    response_generator = send_request_to_ollama_api(agent_name, prompt)

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
    )  # Remove non-alphanumeric characters
    formatted_expert_name = (
        formatted_expert_name.lower().replace(" ", "_")
    )  # Convert to lowercase and replace spaces with underscores

    agents_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "agents")
    )
    json_file = os.path.join(agents_dir, f"{formatted_expert_name}.json")

    if os.path.exists(json_file):
        with open(json_file, "r") as f:
            file_content = f.read()

        b64_content = base64.b64encode(file_content.encode()).decode()

        href = f'Download {formatted_expert_name}.json'
        st.markdown(href, unsafe_allow_html=True)
    else:
        st.error(f"File not found: {json_file}")