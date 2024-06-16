# TeamForgeAI/agent_display.py
import os
import streamlit as st
from file_utils import load_agents_from_json, save_agent_to_json, load_skills
from agent_interactions import process_agent_interaction
from ui.utils import extract_keywords
from agent_edit import (
    open_edit_agent, delete_agent, remove_agent_from_ui, handle_agent_editing,
    sanitize_agent_name, assign_skills, select_model
)
from ui.discussion import update_discussion_and_whiteboard

def reload_agents() -> None:
    """Reloads the agents from the JSON files."""
    agents_base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "TeamForgeAI", "files", "agents"))
    st.session_state["agents_data"] = load_agents_from_json(
        os.path.join(agents_base_dir, st.session_state["current_team"])
    )
    st.session_state["trigger_rerun"] = True

def agent_button_callback(agent_index: int):
    """Callback function for when an agent button is clicked."""
    def callback() -> None:
        """Handles the agent interaction when the button is clicked."""
        st.session_state["selected_agent_index"] = agent_index
        agent = st.session_state.agents_data[agent_index]
        agent_name = agent.get("config", {}).get("name", "")
        st.session_state["form_agent_name"] = agent_name
        st.session_state["form_agent_description"] = agent.get("description", "")

        if st.session_state.get("show_edit"):
            return  # Do nothing if the edit panel is open

        selected_skill = agent.get("skill", [])

        if selected_skill:
            available_skills = load_skills()
            if selected_skill[0] in available_skills:
                skill_function = available_skills[selected_skill[0]]
                user_input = st.session_state.get("user_input", "")
                rephrased_request = st.session_state.get("rephrased_request", "")
                discussion_history = st.session_state.get("discussion_history", "")
                agents_data = st.session_state.get("agents_data", [])  # Get agents_data from session state

                if selected_skill[0] == "web_search":
                    keywords = extract_keywords(rephrased_request) + extract_keywords(discussion_history)
                    query = " ".join(keywords)
                elif selected_skill[0] == "generate_sd_images":
                    query = discussion_history
                elif selected_skill[0] == "plot_diagram":
                    query = "{}"
                elif selected_skill[0] in ["generate_agent_instructions", "update_project_status"]:
                    query = ""
                else:
                    query = user_input

                teachability = agent.get("teachability", False)

                if selected_skill[0] == "generate_sd_images":
                    skill_result = skill_function(discussion_history=discussion_history)
                elif selected_skill[0] == "fetch_web_content":
                    skill_result = skill_function(query=query, discussion_history=discussion_history, teachability=teachability)
                elif selected_skill[0] == "plot_diagram":
                    skill_result = skill_function(query=query, discussion_history=discussion_history)
                elif selected_skill[0] == "web_search":
                    # Pass agents_data and teachability to web_search
                    skill_result = skill_function(query=query, discussion_history=discussion_history, agents_data=agents_data, teachability=teachability)
                else:
                    skill_result = skill_function(query=query, agents_data=st.session_state.agents_data, discussion_history=discussion_history)

                if selected_skill[0] == "generate_sd_images":
                    pass
                elif selected_skill[0] == "plot_diagram":
                    if skill_result.startswith("Error:"):
                        st.error(skill_result)
                    else:
                        st.image(skill_result, caption="Generated Diagram")
                else:
                    if isinstance(skill_result, list):
                        # Unpack four elements: title, url, snippet, content
                        formatted_results = "\n".join(
                            [f"- {title}: {url} ({snippet})\nContent: {content}" for title, url, snippet, content in skill_result]
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

    teams = ["agents"] + [
        folder for folder in os.listdir(agents_base_dir)
        if os.path.isdir(os.path.join(agents_base_dir, folder))
    ]

    # Initialize agents_data
    agents_data = st.session_state.get("agents_data", [])

    # Load agents from files if agents_data is empty
    if not agents_data:
        st.session_state["agents_data"] = load_agents_from_json(
            os.path.join(agents_base_dir, st.session_state["current_team"])
        )
        agents_data = st.session_state["agents_data"] # Update agents_data after loading

    if agents_data:
        st.sidebar.title("Your Agents")
        st.sidebar.subheader("Click to interact")

        for index, agent in enumerate(agents_data):
            agent_name = agent["config"].get("name", f"Unnamed Agent {index + 1}")

            column1, column2, column3, column4 = st.sidebar.columns([1, 1, 1, 5])
            with column1:
                if st.button("⚙️", key=f"gear_{index}", on_click=lambda i=index: open_edit_agent(i)):
                    pass
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
                        button_style + f'<button class="custom-button active">{agent.get("emoji", "🐶")} {agent_name}</button>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.button(
                        f'{agent.get("emoji", "🐶")} {agent_name}',
                        key=f"agent_{index}",
                        on_click=agent_button_callback(index),
                    )

    handle_agent_editing(teams, agents_base_dir)

    new_agent_role = st.sidebar.text_input("New Agent Role", key="new_agent_role")
    if st.sidebar.button("Add Agent", key="add_agent"):
        new_agent_skills = assign_skills(new_agent_role)
        new_agent_model = select_model(new_agent_skills)
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
            "ollama_url": "http://localhost:11434",
            "temperature": 0.20,
            "model": new_agent_model,
        }
        st.session_state.agents_data.append(new_agent)
        save_agent_to_json(
            new_agent,
            os.path.join(agents_base_dir, st.session_state["current_team"], f"{new_agent['config']['name']}.json"),
        )
        st.session_state["trigger_rerun"] = True

    st.sidebar.title("Team Management")
    new_team_name = st.sidebar.text_input("New Team Name", key="new_team_name")
    if st.sidebar.button("Create Team", key="create_team"):
        team_dir = os.path.join(agents_base_dir, new_team_name)
        if not os.path.exists(team_dir):
            os.makedirs(team_dir)
            st.session_state["trigger_rerun"] = True

    selected_team = st.sidebar.selectbox("Select Team", teams, key="selected_agent_team", on_change=reload_agents)
    st.session_state["current_team"] = selected_team

    if st.session_state.get("trigger_rerun", False):
        st.session_state["trigger_rerun"] = False
        st.rerun()
