# TeamForgeAI/main.py
import os
import time
from datetime import datetime
import base64  # Import the base64 module

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
from api_utils import get_ollama_models # Import get_ollama_models from api_utils.py

from current_project import CurrentProject  # Import CurrentProject from current_project.py


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
if "selected_background" not in st.session_state:
    st.session_state.selected_background = ""  # Ensure it's defined

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


# --- Function to format markdown with background image ---
def background_markdown(background_image):
    return f"""
    <style>
    /* General styles */
    body {{
        font-family: 'Courier New', sans-serif!important;
        background-color: #f0f0f0;
    }}
    /* Sidebar styles */
    .sidebar .sidebar-content {{
        background-color: #ffffff !important;
        padding: 0px !important;
        border-radius: 5px !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1) !important;
    }}
    h1 {{
        font-size: 40px !important;
        color: #666666 !important;
        font-family: 'Open Sans'!important;
    }}
    h2 {{
        font-size: 16px !important;
        color: #666666 !important;
        font-family: 'Open Sans'!important;
    }}
    .logo {{
        font-size: 50px !important;
        color: red!important;
    }}
    .sidebar .stButton button {{
        display: block !important;
        width: 100% !important;
        padding: 0px !important;
        background-color: #007bff !important;
        color: #ffffff !important;
        text-align: center !important;
        text-decoration: none !important;
        border-radius: 5px !important;
        transition: background-color 0.3s !important;
    }}
    .sidebar .stButton button:hover {{
        background-color: #0056b3 !important;
    }}
    .sidebar a {{
        display: block !important;       color: #007bff !important;
        text-decoration: none !important;
    }}
    .sidebar a:hover {{
        text-decoration: underline !important;
    }}
    /* Main content styles */
    .main .stTextInput input {{
        width: 100% !important;
        padding: 10px !important;
        border: 1px solid #cccccc !important;
        border-radius: 5px !important;
        font-family: 'Courier New', sans-serif!important;
    }}
    .main .stTextArea textarea {{
        width: 100% !important;
        padding: 10px !important;
        border: 1px solid #cccccc !important;
        border-radius: 5px !important;
        resize: none !important;
        font-family: 'Courier New', sans-serif!important;
    }}
    button {{
        padding: 8px !important;
        color: #ffffff ! important;
        cursor: pointer !important;
        margin: 0!important;
    }}
    .main .stButton button {{
        padding: 0px 0px !important;
        background-color: #dc3545 !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 5px !important;
        cursor: pointer !important;
        transition: background-color 0.3s !important;
    }}
    .main .stButton button:hover {{
        background-color: #c82333 !important;
    }}
    /* Model selection styles */
    .main .stSelectbox select {{
        width: 100% !important;
        padding: 3px !important;
        border: 1px solid #cccccc !important;
        border-radius: 5px !important;
        font-family: 'Open Sans'!important;
    }}
    /* Error message styles */
    .main .stAlert {{
        color: #333 !important;
    }}
    /* Virtual Office Styles */
    .virtual-office {{
        width: 100%;
        height: 300px; 
        border: 1px solid #ccc;
        position: relative;
        overflow: hidden;
        background-image: url('data:image/png;base64,{background_image}');
        background-size: cover;
        background-position: center;
    }}
    .virtual-office::before {{
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.5); /* Black overlay with 50% opacity */
        z-index: 1;
    }}
    .agent-emoji {{
        font-size: 40px; /* Default size */
        position: absolute;
        transition: left 1s, top 1s, font-size 0.5s; /* Adjust animation duration */
        filter: brightness(0.8); /* Adjust the brightness value as needed */
        z-index: 2;
    }}
    .agent-emoji.active {{
        font-size: 60px;
        filter: brightness(1.1); /* Adjust the brightness value as needed */
    }}
    /* Speech Bubble Styles */
    .speech-bubble {{
        position: absolute;
        background-color: #333;
        color: #ccc;
        border-radius: 10px;
        padding: 6px;
        font-size: 14px;
        margin-top: 16px;
        margin-left: 20px;
        display: none;
        z-index: 3;
    }}
    .agent-emoji.active + .speech-bubble {{
        display: block; /* Show only for active agent */
    }}
    /* Ensuring minimum height for the Virtual Office column */
    .virtual-office-column {{
        display: flex;
        flex-direction: column;
        justify-content: center;
    }}
    </style>
    """

def display_virtual_office(background_image):
    """Displays the virtual office with animated emojis."""
    agents_data = st.session_state.get("agents_data", [])
    active_agent_name = st.session_state.get("next_agent", None)  # Get the active agent
    last_comment = st.session_state.get("last_comment", "")[:90]  # Get the last comment (first 50 characters)

    office_html = """
    <div class="virtual-office">
        {}  
    </div>
    """

    agent_emojis = ""
    # Only create emojis if there are agents in agents_data
    if agents_data:
        for i, agent_data in enumerate(agents_data):
            agent_name = agent_data["config"].get("name", f"Agent {i+1}")
            agent_emoji = agent_data.get("emoji", "❓")

            # Apply active class if the agent is the active agent
            active_class = "active" if agent_name == active_agent_name else ""

            if agent_name == active_agent_name:
                # Active agent at the top
                left_pos = 130  # Centered horizontally
                top_pos = 20
            else:
                # Other agents mill around below - Adjusted vertical range
                left_pos = random.randint(10, 250)
                top_pos = random.randint(120, 270)  

            agent_emojis += f'<span id="agent-{i}" class="agent-emoji {active_class}" style="left: {left_pos}px; top: {top_pos}px;">{agent_emoji}</span>'
            # Add speech bubble for the active agent with the last comment and '...'
            if active_class:
                agent_emojis += f'<div class="speech-bubble" style="left: {left_pos + 40}px; top: {top_pos - 30}px;">{last_comment}...</div>'

    # --- Call markdown before the office_html ---
    st.markdown(background_markdown(background_image), unsafe_allow_html=True)
    st.markdown(office_html.format(agent_emojis), unsafe_allow_html=True)

    # --- Move JavaScript for animation after the virtual office HTML ---
    animation_script = """
    <script>
    function animateAgents() {
        const agents = document.querySelectorAll('.agent-emoji');
        const activeAgent = '""" + (active_agent_name.replace(" ", "_") if active_agent_name else "") + """'; 

        agents.forEach(agent => {
            if (agent.id.includes(activeAgent)) return; // Don't animate the active agent

            const leftPos = Math.random() * (250 - 10) + 10;
            const topPos = Math.random() * (270 - 160) + 120; // Adjust vertical range
            agent.style.left = leftPos + 'px';
            agent.style.top = topPos + 'px';
        });
    }
    setInterval(animateAgents, 1000); // Adjust animation interval
    </script>
    """

    st.markdown(animation_script, unsafe_allow_html=True)

def load_background_images(folder_path: str) -> dict:
    """Loads background images from the specified folder."""
    background_images = {}
    for filename in os.listdir(folder_path):
        if filename.endswith((".png", ".jpg", ".jpeg")):
            image_path = os.path.join(folder_path, filename)
            with open(image_path, "rb") as f:
                image_data = f.read()
                background_images[filename] = base64.b64encode(image_data).decode("utf-8")
    return background_images

class CurrentProject:
    def __init__(self):
        self.re_engineered_prompt = ""
        self.objectives = []
        self.deliverables = []
        self.goal = ""

    def set_re_engineered_prompt(self, prompt):
        self.re_engineered_prompt = prompt

    def add_objective(self, objective):
        self.objectives.append({"text": objective, "done": False})

    def add_deliverable(self, deliverable):
        self.deliverables.append({"text": deliverable, "done": False})

    def set_goal(self, goal):
        self.goal = goal

    def mark_objective_done(self, index):
        if 0 <= index < len(self.objectives):
            self.objectives[index]["done"] = True

    def mark_deliverable_done(self, index):
        if 0 <= index < len(self.deliverables):
            self.deliverables[index]["done"] = True

    def mark_objective_undone(self, index):
        if 0 <= index < len(self.objectives):
            self.objectives[index]["done"] = False

    def mark_deliverable_undone(self, index):
        if 0 <= index < len(self.deliverables):
            self.deliverables[index]["done"] = False

def main():
    col1, col2 = st.columns([3, 2])
    with col1:
        # Load background images
        background_images = load_background_images("TeamForgeAI/images")

        # Ensure a random background image is picked on load
        if not st.session_state.selected_background:
            st.session_state.selected_background = random.choice(list(background_images.keys()))

        # Prepare sorted list of background images without file extensions
        background_names = [os.path.splitext(name)[0] for name in sorted(background_images.keys())]

        # Allow the user to choose a background image
        selected_background_name = st.selectbox("Agent Workspace Theme", background_names, key="selected_background_name")

        # Match the selected name with the actual file name (restore the extension)
        st.session_state.selected_background = next(filename for filename in background_images.keys() if os.path.splitext(filename)[0] == selected_background_name)

        # Display the virtual office with the selected background
        st.markdown('<div class="virtual-office-column">', unsafe_allow_html=True)
        display_virtual_office(background_images.get(st.session_state.selected_background, "default.png"))
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        display_user_request_input()
        display_rephrased_request()
        display_user_input()

    col3, col4, col5 = st.columns([3, 3, 3])
    with col3:
        st.text_input(
            "Endpoint",
            value=st.session_state.ollama_url_input,
            key="ollama_url_input",
        )
        st.session_state.ollama_url = st.session_state.ollama_url_input

    with col4:
        temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=1.0,
            value=st.session_state.get("temperature", 0.1),
            step=0.01,
            key="temperature",
        )

    with col5:
        available_models = get_ollama_models(st.session_state.ollama_url) # Pass the endpoint to get_ollama_models
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
            '<h1 class="logo">🦊🐻🐹 Team<span style="color: orange;">Forge</span><span style="color: yellow;">AI</span></h1>'
            "</div>",
            unsafe_allow_html=True,
        )

        display_agents()

    with st.container():
        display_discussion_and_whiteboard()

        # Append new comments from 'last_comment' to the discussion history
        if st.session_state.last_comment and st.session_state.last_comment not in st.session_state.discussion_history:
            st.session_state.discussion_history += "\n" + st.session_state.last_comment

        if st.session_state.last_request:
            st.write("Last Request:")
            st.write(st.session_state.last_request)

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
