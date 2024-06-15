# TeamForgeAI/inputs.py
import re
from ui.utils import handle_begin # Corrected import
import streamlit as st

from agent_utils import get_agents_from_text, get_workflow_from_agents, zip_files_in_memory

def display_user_input() -> str:
    """Displays a text area for user input and extracts URLs."""
    user_input = st.text_area("Additional Input:", key="user_input", height=100)
    if user_input:
        url_pattern = re.compile(
            r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
        )
        url_match = url_pattern.search(user_input)
        if url_match:
            st.session_state.reference_url = url_match.group()
        else:
            st.session_state.reference_url = ""
    else:
        st.session_state.reference_url = ""
    return user_input


def display_rephrased_request() -> None:
    """Displays the rephrased user request in a text area."""
    st.text_area(
        "Re-engineered Prompt:",
        value=st.session_state.get("rephrased_request", ""),
        height=100,
        key="rephrased_request_area",
    )


def display_user_request_input() -> None:
    """Displays the user request input field and triggers agent creation."""
    user_request = st.text_input(
        "Enter your request:",
        key="user_request",
        value=st.session_state.get("user_request", ""),
    )
    if st.session_state.get("previous_user_request") != user_request:
        st.session_state.previous_user_request = user_request
        if user_request:
            try:
                if not st.session_state.get("rephrased_request"):
                    handle_begin(st.session_state)
                else:
                    autogen_agents, crewai_agents, _ = get_agents_from_text(
                        st.session_state.rephrased_request
                    )
                    print(f"Debug: AutoGen Agents: {autogen_agents}")
                    print(f"Debug: CrewAI Agents: {crewai_agents}")
                    if not autogen_agents:
                        print("Error: No agents created.")
                        st.warning("Failed to create agents. Please try again.")
                        return
                    agents_data = {}
                    for agent in autogen_agents:
                        agent_name = agent["config"]["name"]
                        agents_data[agent_name] = agent
                    print(f"Debug: Agents data: {agents_data}")
                    workflow_data, _ = get_workflow_from_agents(autogen_agents)
                    print(f"Debug: Workflow data: {workflow_data}")
                    print(f"Debug: CrewAI agents: {crewai_agents}")
                    (
                        autogen_zip_buffer,
                        crewai_zip_buffer,
                    ) = zip_files_in_memory(agents_data, workflow_data, crewai_agents)
                    st.session_state.autogen_zip_buffer = autogen_zip_buffer
                    st.session_state.crewai_zip_buffer = crewai_zip_buffer
                    st.session_state.agents_data = autogen_agents # Update the session state variable
            except Exception as e:
                print(f"Error in display_user_request_input: {e}")
    # Trigger a re-run of the Streamlit app outside the conditional block
    if st.session_state.get("trigger_rerun"):
        st.session_state["trigger_rerun"] = False
        st.rerun()
