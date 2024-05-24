import os
import time
from datetime import datetime

import requests
import streamlit as st
import random

from agent_management import display_agents
from ui.discussion import (
    display_discussion_and_whiteboard,
    update_discussion_and_whiteboard,
)
from ui.inputs import (
    display_user_input,
    display_rephrased_request,
    display_user_request_input,
)
from ui.utils import (
    get_api_key,
    display_download_button,
    rephrase_prompt,
    get_agents_from_text,
    extract_code_from_response,
    get_workflow_from_agents,
    zip_files_in_memory,
)
from custom_button import agent_button
from agent_interactions import generate_and_display_image

# Set up the page to use a wide layout
st.set_page_config(layout="wide")

# Initialize session state variables if they are not already present
if "trigger_rerun" not in st.session_state:
    st.session_state.trigger_rerun = False
if "whiteboard" not in st.session_state:
    st.session_state.whiteboard = ""
if "last_comment" not in st.session_state:
    st.session_state.last_comment = ""
if "discussion_history" not in st.session_state:
    st.session_state.discussion_history = ""
if "rephrased_request" not in st.session_state:
    st.session_state.rephrased_request = ""
if "need_rerun" not in st.session_state:
    st.session_state.need_rerun = False
if "ollama_url" not in st.session_state:
    st.session_state.ollama_url = "http://localhost:11434"
if "ollama_url_input" not in st.session_state:
    st.session_state.ollama_url_input = st.session_state.ollama_url
if "selected_model" not in st.session_state:
    st.session_state.selected_model = "mistral:7b-instruct-v0.2-q8_0"  # Default model
if "last_request" not in st.session_state:  # Initialize last_request
    st.session_state.last_request = ""
if "user_request" not in st.session_state:
    st.session_state.user_request = ""
if "user_input" not in st.session_state:
    st.session_state.user_input = ""
if "selected_discussion" not in st.session_state:
    st.session_state.selected_discussion = ""
if "current_discussion" not in st.session_state:
    st.session_state.current_discussion = ""

# Directory for saving discussion history
project_dir = 'project'
if not os.path.exists(project_dir):
    os.makedirs(project_dir)

def save_discussion_history(history, discussion_name):
    with open(os.path.join(project_dir, f"{discussion_name}.txt"), 'w') as f:  # Write mode to avoid duplication
        f.write(history)
    cleanup_old_files(project_dir, max_files=20)

def load_discussion_history(discussion_name):
    file_path = os.path.join(project_dir, f"{discussion_name}.txt")
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return f.read()
    return ""

def list_discussions():
    return [f.replace('.txt', '') for f in os.listdir(project_dir) if os.path.isfile(os.path.join(project_dir, f))]

def cleanup_old_files(directory, max_files):
    files = [os.path.join(directory, f) for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
    files.sort(key=os.path.getmtime, reverse=True)
    for old_file in files[max_files:]:
        os.remove(old_file)

# Load selected discussion into session state
if st.session_state.selected_discussion:
    loaded_history = load_discussion_history(st.session_state.selected_discussion)
    st.session_state.discussion_history = loaded_history

st.markdown(
    """
    <style>
    /* General styles */
    body {
        font-family: 'Courier New', sans-serif!important;
        background-color: #f0f0f0;
    }
    /* Sidebar styles */
    .sidebar .sidebar-content {
        background-color: #ffffff !important;
        padding: 0px !important;
        border-radius: 5px !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1) !important;
    }
    h1 {
        font-size: 40px !important;
        color: #666666 !important;
        font-family: 'Open Sans'!important;
    }
    h2 {
        font-size: 16px !important;
        color: #666666 !important;
        font-family: 'Open Sans'!important;
    }
    .logo {
        font-size: 50px !important;
        color: red!important;
    }
    .sidebar .stButton button {
        display: block !important;
        width: 100% !important;
        padding: 0px !important;
        background-color: #007bff !important;
        color: #ffffff !important;
        text-align: center !important;
        text-decoration: none !important;
        border-radius: 5px !important;
        transition: background-color 0.3s !important;
    }
    .sidebar .stButton button:hover {
        background-color: #0056b3 !important;
    }
    .sidebar a {
        display: block !important;
        color: #007bff !important;
        text-decoration: none !important;
    }
    .sidebar a:hover {
        text-decoration: underline !important;
    }
    /* Main content styles */
    .main .stTextInput input {
        width: 100% !important;
        padding: 10px !important;
        border: 1px solid #cccccc !important;
        border-radius: 5px !important;
        font-family: 'Courier New', sans-serif!important;
    }
    .main .stTextArea textarea {
        width: 100% !important;
        padding: 10px !important;
        border: 1px solid #cccccc !important;
        border-radius: 5px !important;
        resize: none !important;
        font-family: 'Courier New', sans-serif!important;
    }
    button {
        padding: 8px !important;
        color: #ffffff ! important;
        cursor: pointer !important;
        margin: 0!important;
    }
    .main .stButton button {
        padding: 0px 0px !important;
        background-color: #dc3545 !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 5px !important;
        cursor: pointer !important;
        transition: background-color 0.3s !important;
    }
    .main .stButton button:hover {
        background-color: #c82333 !important;
    }
    /* Model selection styles */
    .main .stSelectbox select {
        width: 100% !important;
        padding: 3px !important;
        border: 1px solid #cccccc !important;
        border-radius: 5px !important;
        font-family: 'Open Sans'!important;
    }
    /* Error message styles */
    .main .stAlert {
        color: #333 !important;
    }
    /* Virtual Office Styles */
    .virtual-office {
        width: 300px; 
        height: 200px; 
        border: 1px solid #ccc;
        position: relative;
        overflow: hidden;
    }
    .agent-emoji {
        font-size: 36px;
        position: absolute;
        transition: left 1s, top 1s; /* Adjust animation duration */
    }
    </style>
    """,
    unsafe_allow_html=True,
)

def get_ollama_models():
    try:
        response = requests.get(f"{st.session_state.ollama_url}/api/tags")
        response.raise_for_status()
        models = [
            model["name"]
            for model in response.json()["models"]
            if "embed" not in model["name"]
        ]
        models.sort()  # Simple alphabetical sorting for now
        return models
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching models: {e}")
        return []

def display_virtual_office():
    """Displays the virtual office with animated emojis."""
    agents_data = st.session_state.get("agents_data", [])
    active_agent_name = st.session_state.get("next_agent", None)  # Get the active agent

    office_html = """
    <div class="virtual-office">
        {}  
    </div>
    """

    agent_emojis = ""
    for i, agent_data in enumerate(agents_data):
        agent_name = agent_data["config"].get("name", f"Agent {i+1}")
        agent_emoji = agent_data.get("emoji", "❓")

        if agent_name == active_agent_name:
            # Active agent at the top
            left_pos = 130  # Centered horizontally
            top_pos = 20
        else:
            # Other agents mill around below
            left_pos = random.randint(10, 250)
            top_pos = random.randint(80, 150)  # Adjust vertical range

        agent_emojis += f'<span id="agent-{i}" class="agent-emoji" style="left: {left_pos}px; top: {top_pos}px;">{agent_emoji}</span>'

    st.markdown(office_html.format(agent_emojis), unsafe_allow_html=True)

    # JavaScript for animation (using string concatenation instead of .format())
    animation_script = """
    <script>
    function animateAgents() {
        const agents = document.querySelectorAll('.agent-emoji');
        const activeAgent = '""" + (active_agent_name.replace(" ", "_") if active_agent_name else "") + """'; 

        agents.forEach(agent => {
            if (agent.id.includes(activeAgent)) return; // Don't animate the active agent

            const leftPos = Math.random() * (250 - 10) + 10;
            const topPos = Math.random() * (150 - 80) + 80; // Adjust vertical range
            agent.style.left = leftPos + 'px';
            agent.style.top = topPos + 'px';
        });
    }
    setInterval(animateAgents, 1000); // Adjust animation interval
    </script>
    """

    st.markdown(animation_script, unsafe_allow_html=True)

def main():
    col1, col2, col3 = st.columns([3, 3, 3])
    with col1:
        st.text_input(
            "Endpoint",
            value=st.session_state.ollama_url_input,
            key="ollama_url_input",
        )
        st.session_state.ollama_url = st.session_state.ollama_url_input

    with col2:
        temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=1.0,
            value=st.session_state.get("temperature", 0.1),
            step=0.01,
            key="temperature",
        )


    with col3:
        available_models = get_ollama_models()
        st.session_state.selected_model = st.selectbox(
            "Model",
            options=available_models,
            index=available_models.index(st.session_state.selected_model)
            if st.session_state.selected_model in available_models
            else 0,
            key="model_selection",
        )
        st.query_params["model"] = [st.session_state.selected_model]  # Correct syntax
        st.session_state.model = st.session_state.selected_model  # Update model in session state
        
    with st.sidebar:
        st.markdown(
            '<div style="text-align: center;">'
            '<h1 class="logo">🦊🐻🐹 TeamForgeAI</h1>'
            "</div>",
            unsafe_allow_html=True,
        )

        display_agents()

    with st.container():
        display_virtual_office()
        
        display_user_request_input()
        display_rephrased_request()


        display_discussion_and_whiteboard()

        # Append new comments from 'last_comment' to the discussion history
        if st.session_state.last_comment and st.session_state.last_comment not in st.session_state.discussion_history:
            st.session_state.discussion_history += "\n" + st.session_state.last_comment

        if st.session_state.last_request:
            st.write("Last Request:")
            st.write(st.session_state.last_request)

        display_user_input()
        discussions = list_discussions()
        selected_discussion = st.selectbox("Load Previous Discussion", [""] + discussions, index=0)
        if selected_discussion:
            st.session_state.selected_discussion = selected_discussion
            st.session_state.discussion_history = load_discussion_history(selected_discussion)
        display_download_button()

        if st.session_state.get("generate_image", False):
            query = st.session_state.get("discussion_history", "")
            generate_and_display_image(query)
            st.session_state["generate_image"] = False  # Reset the flag

    # Save discussion history whenever it changes
    if st.session_state.discussion_history:
        save_discussion_history(st.session_state.discussion_history, st.session_state.selected_discussion or f"discussion_{datetime.now().strftime('%Y%m%d_%H%M%S')}")

    if st.session_state.trigger_rerun:
        st.session_state.trigger_rerun = False  # Reset the flag
        st.rerun()  # Now call rerun

if __name__ == "__main__":
    main()
