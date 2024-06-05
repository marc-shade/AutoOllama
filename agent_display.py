# TeamForgeAI/agent_display.py
import os  # Import the os module
import streamlit as st

from file_utils import load_agents_from_json, save_agent_to_json, load_skills  # Added import here
from agent_interactions import process_agent_interaction
from ui.utils import extract_keywords
from agent_edit import open_edit_agent, delete_agent, remove_agent_from_ui, handle_agent_editing, sanitize_agent_name, assign_skills, select_model  # Import from agent_edit.py
from ui.discussion import update_discussion_and_whiteboard  # Added import here

def reload_agents() -> None:
    """Reloads the agents from the JSON files."""
    agents_base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "TeamForgeAI", "files", "agents"))
    st.session_state["agents_data"] = load_agents_from_json(
        os.path.join(agents_base_dir, st.session_state["current_team"])  # Corrected path
    )
    # --- Trigger a re-run ---
    st.session_state["trigger_rerun"] = True 

def agent_button_callback(agent_index: int):
    """Callback function for when an agent button is clicked."""

    def callback() -> None:
        """Handles the agent interaction when the button is clicked."""
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

        # --- Check if the edit button was clicked ---
        if st.session_state.get("show_edit"):
            return  # Do nothing if the edit panel is open

        # --- Get the agent's selected skill ---
        selected_skill = agent.get("skill", []) # Ensure selected_skill is a list

        # --- Execute the skill directly if it's assigned ---
        if selected_skill:
            available_skills = load_skills()
            if selected_skill[0] in available_skills: # Check the first skill in the list
                skill_function = available_skills[selected_skill[0]]

                # --- Prepare the query based on the skill ---
                user_input = st.session_state.get("user_input", "")
                rephrased_request = st.session_state.get("rephrased_request", "")
                discussion_history = st.session_state.get("discussion_history", "")  # Get the discussion history
                if selected_skill[0] == "web_search":
                    keywords = extract_keywords(rephrased_request) + extract_keywords(
                        st.session_state.get("discussion_history", "")
                    )
                    query = " ".join(keywords)
                elif selected_skill[0] == "generate_sd_images":
                    query = discussion_history  # Pass the discussion history to generate_sd_images
                elif selected_skill[0] == "plot_diagram":
                    query = "{}"
                # --- Pass user_input to all skills ---
                elif selected_skill[0] in ["generate_agent_instructions", "update_project_status"]:  # Handle new skills
                    query = ""  # These skills don't require a query
                else: 
                    query = user_input

                # --- Execute the skill ---
                if selected_skill[0] == "generate_sd_images":
                    skill_result = skill_function(discussion_history=discussion_history)  # Pass only discussion_history
                elif selected_skill[0] == "fetch_web_content":  # Handle fetch_web_content separately
                    skill_result = skill_function(query=query)  # Pass only query to fetch_web_content
                elif selected_skill[0] == "plot_diagram":  # Handle plot_diagram separately
                    skill_result = skill_function(query=query)  # Pass only query to plot_diagram
                elif selected_skill[0] == "web_search":
                    skill_result = skill_function(query=query)  # Pass only query to web_search
                else:
                    skill_result = skill_function(query=query, agents_data=st.session_state.agents_data)  # Pass query for other skills

                # --- Handle the skill result ---
                if selected_skill[0] == "generate_sd_images":
                    pass
                elif selected_skill[0] == "plot_diagram":
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
                        response_text = f"Skill '{selected_skill[0]}' result: {skill_result}"

                    update_discussion_and_whiteboard(agent_name, response_text, user_input)

        else:
            process_agent_interaction(agent_index)

    return callback


def display_agents() -> None:
    """Displays the agents in the sidebar."""
    if st.session_state.get("trigger_rerun", False):
        st.session_state["trigger_rerun"] = False
        st.rerun()

    agents_base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "TeamForgeAI", "files", "agents"))
    if "current_team" not in st.session_state:
        st.session_state["current_team"] = "agents"

    # Define teams here, outside the conditional block
    teams = ["agents"] + [
        f"{folder}"
        for folder in os.listdir(agents_base_dir)
        if os.path.isdir(os.path.join(agents_base_dir, folder))
    ]

    # Agent Loading and Display
    if "agents_data" not in st.session_state:
        st.session_state["agents_data"] = load_agents_from_json(
            os.path.join(agents_base_dir, st.session_state["current_team"])  # Corrected path
        )

    agents_data = st.session_state["agents_data"]
    
    if agents_data:
        st.sidebar.title("Your Agents")
        st.sidebar.subheader("Click to interact")

        # --- Force the sidebar to update when agents are added ---
        for index, agent in enumerate(agents_data):
            agent_name = (
                agent["config"]["name"]
                if agent["config"].get("name")
                else f"Unnamed Agent {index + 1}"
            )

            column1, column2, column3, column4 = st.sidebar.columns([1, 1, 1, 5])
            with column1:
                if st.button("⚙️", key=f"gear_{index}", on_click=lambda i=index: open_edit_agent(i)):
                    pass  # Removed st.rerun() from here
            with column2:
                if st.button("🗑️", key=f"delete_{index}", on_click=lambda i=index: delete_agent(i)):
                    pass
            with column3:
                if st.button("🚫", key=f"remove_{index}", on_click=lambda i=index: remove_agent_from_ui(i)):
                    pass

            with column4:
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
    
    handle_agent_editing(teams, agents_base_dir)  # Pass agents_base_dir

    # Add Agent Section
    new_agent_role = st.sidebar.text_input("New Agent Role", key="new_agent_role")
    if st.sidebar.button("Add Agent", key="add_agent"):
        new_agent_skills = assign_skills(new_agent_role)  # Assign skills based on role
        new_agent_model = select_model(new_agent_skills)  # Select model based on skills
        # --- Sanitize the agent name ---
        new_agent_role = sanitize_agent_name(new_agent_role)
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
            os.path.join(agents_base_dir, st.session_state["current_team"], f"{new_agent['config']['name']}.json"),
        )
        # --- Set the flag to trigger a rerun ---
        st.session_state["trigger_rerun"] = True

    # Team Management Section
    st.sidebar.title("Team Management")
    new_team_name = st.sidebar.text_input("New Team Name", key="new_team_name")
    if st.sidebar.button("Create Team", key="create_team"):
        team_dir = os.path.join(agents_base_dir, new_team_name)
        if not os.path.exists(team_dir):
            os.makedirs(team_dir)
            st.session_state["trigger_rerun"] = True

    # Team Selection (Moved under Team Management)
    selected_team = st.sidebar.selectbox("Select Team", teams, key="selected_agent_team", on_change=reload_agents)
    st.session_state["current_team"] = selected_team

    # --- Trigger a rerun if agents were updated ---
    if st.session_state.get("trigger_rerun", False):
        st.session_state["trigger_rerun"] = False
        st.rerun()  # Moved st.rerun() here
