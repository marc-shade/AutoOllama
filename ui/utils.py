# TeamForgeAI/ui/utils.py

import os
import time
import streamlit as st
import pandas as pd
import re
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from file_utils import create_agent_data, sanitize_text, load_skills, save_agent_to_json
from agent_utils import rephrase_prompt, get_agents_from_text, get_workflow_from_agents, zip_files_in_memory

# Directory for saving discussion history
PROJECT_DIR = 'TeamForgeAI/files/discussions'
if not os.path.exists(PROJECT_DIR):
    os.makedirs(PROJECT_DIR)

def list_discussions() -> list:
    """Lists all saved discussions."""
    return [f.replace('.txt', '') for f in os.listdir(PROJECT_DIR) if os.path.isfile(os.path.join(PROJECT_DIR, f))]

def load_discussion_history(discussion_name: str) -> str:
    """Loads the discussion history from a text file."""
    file_path = os.path.join(PROJECT_DIR, f"{discussion_name}.txt")
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding="utf-8") as file:
            return file.read()
    return ""

def save_discussion_history(history: str, discussion_name: str) -> None:
    """Saves the discussion history to a text file."""
    with open(os.path.join(PROJECT_DIR, f"{discussion_name}.txt"), 'w', encoding="utf-8") as file:
        file.write(history)
    cleanup_old_files(PROJECT_DIR, max_files=20)

def cleanup_old_files(directory: str, max_files: int) -> None:
    """Deletes old files from the specified directory, keeping only the most recent ones."""
    files = [os.path.join(directory, file) for file in os.listdir(directory) if os.path.isfile(os.path.join(directory, file))]
    files.sort(key=os.path.getmtime, reverse=True)
    for old_file in files[max_files:]:
        os.remove(old_file)

def extract_keywords(text: str) -> list:
    """Extracts keywords from the provided text."""
    stop_words = set(stopwords.words('english'))  # Define English stop words
    words = word_tokenize(text) # Tokenize the text
    keywords = [word for word in words if word.lower() not in stop_words and word.isalnum()] # Filter keywords
    return keywords

def get_api_key() -> str:
    """Returns a hardcoded API key."""
    return "ollama"

def handle_begin(session_state: dict) -> None:
    """Handles the initial processing of the user request."""
    user_request = session_state.user_request
    max_retries = 3
    retry_delay = 2  # in seconds
    for retry in range(max_retries):
        try:
            rephrase_prompt_result = rephrase_prompt(user_request)
            print(f"Debug: Rephrased text: {rephrase_prompt_result}")
            if rephrase_prompt_result:
                session_state.rephrased_request = rephrase_prompt_result
                autogen_agents, crewai_agents, current_project = get_agents_from_text(rephrase_prompt_result) # Modified to return current_project
                print(f"Debug: AutoGen Agents: {autogen_agents}")
                print(f"Debug: CrewAI Agents: {crewai_agents}")
                if not autogen_agents:
                    print("Error: No agents created.")
                    st.warning("Failed to create agents. Please try again.")
                    return
                agents_data = {}
                agents_base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "files", "agents")) # Corrected path
                for agent in autogen_agents:
                    agent_name = agent["config"]["name"]
                    agents_data[agent_name] = agent
                    # --- Save the generated agents to the current team's directory ---
                    save_agent_to_json(
                        agent,
                        os.path.join(agents_base_dir, st.session_state.current_team, f"{agent_name}.json"),
                    )
                print(f"Debug: Agents data: {agents_data}")
                workflow_data, _ = get_workflow_from_agents(autogen_agents)
                print(f"Debug: Workflow data: {workflow_data}")
                print(f"Debug: CrewAI agents: {crewai_agents}")
                (
                    autogen_zip_buffer,
                    crewai_zip_buffer,
                ) = zip_files_in_memory(agents_data, workflow_data, crewai_agents)
                session_state.autogen_zip_buffer = autogen_zip_buffer
                session_state.crewai_zip_buffer = crewai_zip_buffer
                session_state.agents_data = autogen_agents # Now correctly scoped
                session_state.current_project = current_project # Store the current project in session state
                st.session_state["trigger_rerun"] = True # Trigger a rerun
                break  # Exit the loop if successful
            print("Error: Failed to rephrase the user request.")
            st.warning("Failed to rephrase the user request. Please try again.")
            return  # Exit the function if rephrasing fails
        except Exception as error:
            print(f"Error occurred in handle_begin: {str(error)}")
            if retry < max_retries - 1:
                print(f"Retrying in {retry_delay} second(s)...")
                time.sleep(retry_delay)
            else:
                print("Max retries exceeded.")
                st.warning("An error occurred. Please try again.")
                return  # Exit the function if max retries are exceeded            
                
    # --- Recalculate rephrased_text, autogen_agents, crewai_agents, and current_project ---
    rephrased_text = session_state.rephrased_request
    autogen_agents, crewai_agents, current_project = get_agents_from_text(rephrased_text)
    agents_data = {}
    agents_base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "files", "agents")) # Corrected path
    for agent in autogen_agents:
        agent_name = agent["config"]["name"]
        agents_data[agent_name] = agent
        # --- Save the generated agents to the current team's directory ---
        save_agent_to_json(
            agent,
            os.path.join(agents_base_dir, st.session_state.current_team, f"{agent_name}.json"),
        )
    workflow_data, _ = get_workflow_from_agents(autogen_agents)
    (
        autogen_zip_buffer,
        crewai_zip_buffer,
    ) = zip_files_in_memory(agents_data, workflow_data, crewai_agents)
    session_state.autogen_zip_buffer = autogen_zip_buffer
    session_state.crewai_zip_buffer = crewai_zip_buffer
    session_state.agents_data = autogen_agents
    session_state.current_project = current_project # Store the current project in session state
    st.rerun() # Rerun to display the agents

def display_download_button() -> None:
    """Displays download buttons for Autogen and CrewAI files."""
    if "autogen_zip_buffer" in st.session_state and "crewai_zip_buffer" in st.session_state:
        column1, column2 = st.columns(2)
        with column1:
            st.download_button(
                label="Download Autogen Files",
                data=st.session_state.autogen_zip_buffer,
                file_name="autogen_files.zip",
                mime="application/zip",
                key=f"autogen_download_button_{int(time.time())}",
            )
        with column2:
            st.download_button(
                label="Download CrewAI Files",
                data=st.session_state.crewai_zip_buffer,
                file_name="crewai_files.zip",
                mime="application/zip",
                key=f"crewai_download_button_{int(time.time())}",
            )
    else:
        st.warning("No files available for download.")

def display_reset_and_upload_buttons() -> None:
    """Displays buttons for resetting the session and uploading data."""
    column1, column2 = st.columns(2)
    with column1:
        if st.button("Reset", key="reset_button"):
            # Define the keys of session state variables to clear
            keys_to_reset = [
                "rephrased_request",
                "discussion",
                "whiteboard",
                "user_request",
                "user_input",
                "agents",
                "zip_buffer",
                "crewai_zip_buffer",
                "autogen_zip_buffer",
                "uploaded_file_content",
                "discussion_history",
                "last_comment",
                "user_api_key",
                "reference_url",
                "next_agent",
                "selected_agent_index",
                "form_agent_name",
                "form_agent_description",
                "current_project", # Add current_project to the list of keys to reset
            ]
            # Reset each specified key
            for key in keys_to_reset:
                if key in st.session_state:
                    del st.session_state[key]
            st.session_state.user_input = ""
            st.experimental_rerun()
    with column2:
        uploaded_file = st.file_uploader(
            "Upload a sample .csv of your data (optional)", type="csv"
        )
        if uploaded_file is not None:
            try:
                dataframe = pd.read_csv(uploaded_file).head(5)
                st.write("Data successfully uploaded and read as DataFrame:")
                st.dataframe(dataframe)
                st.session_state.uploaded_data = dataframe
            except Exception as error:
                st.error(f"Error reading the file: {error}")

def extract_code_from_response(response: str) -> str:
    """Extracts code blocks from the response."""
    code_pattern = r"```(.*?)```"
    code_blocks = re.findall(code_pattern, response, re.DOTALL)

    html_pattern = r"```(.*?)```"
    code_blocks = re.findall(code_pattern, response, re.DOTALL)

    html_pattern = r"<html.*?>.*?</html>"
    html_blocks = re.findall(html_pattern, response, re.DOTALL | re.IGNORECASE)

    js_pattern = r"<script.*?>.*?</script>"
    js_blocks = re.findall(js_pattern, response, re.DOTALL | re.IGNORECASE)

    css_pattern = r"<style.*?>.*?</style>"
    css_blocks = re.findall(css_pattern, response, re.DOTALL | re.IGNORECASE)

    all_code_blocks = code_blocks + html_blocks + js_blocks + css_blocks
    unique_code_blocks = list(set(all_code_blocks))
    return "\n\n".join(unique_code_blocks)
