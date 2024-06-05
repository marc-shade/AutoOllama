# TeamForgeAI/main.py
import os
from datetime import datetime
import base64  # Import the base64 module

import streamlit as st
import random

# Set up the page to use a wide layout
st.set_page_config(layout="wide")

from agent_display import display_agents # Updated import
from ui.discussion import (
    display_discussion_and_whiteboard,
)
from ui.inputs import (
    display_user_input,
    display_rephrased_request,
    display_user_request_input,
)
from ui.utils import (
    display_download_button,
)
from ui.virtual_office import display_virtual_office, load_background_images # Import from virtual_office.py

from current_project import CurrentProject  # Import CurrentProject from current_project.py



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
if "current_project" not in st.session_state: # Initialize current_project
    st.session_state.current_project = CurrentProject()

# Directory for saving discussion history
PROJECT_DIR = 'TeamForgeAI/files/discussions' # Updated path
if not os.path.exists(PROJECT_DIR):
    os.makedirs(PROJECT_DIR)

def save_discussion_history(history: str, discussion_name: str) -> None:
    """Saves the discussion history to a text file."""
    with open(os.path.join(PROJECT_DIR, f"{discussion_name}.txt"), 'w', encoding="utf-8") as file:  # Write mode to avoid duplication
        file.write(history)
    cleanup_old_files(PROJECT_DIR, max_files=20)

def load_discussion_history(discussion_name: str) -> str:
    """Loads the discussion history from a text file."""
    file_path = os.path.join(PROJECT_DIR, f"{discussion_name}.txt")
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding="utf-8") as file:
            return file.read()
    return ""

def list_discussions() -> list:
    """Lists all saved discussions."""
    return [f.replace('.txt', '') for f in os.listdir(PROJECT_DIR) if os.path.isfile(os.path.join(PROJECT_DIR, f))]

def cleanup_old_files(directory: str, max_files: int) -> None:
    """Deletes old files from the specified directory, keeping only the most recent ones."""
    files = [os.path.join(directory, file) for file in os.listdir(directory) if os.path.isfile(os.path.join(directory, file))]
    files.sort(key=os.path.getmtime, reverse=True)
    for old_file in files[max_files:]:
        os.remove(old_file)

# Load selected discussion into session state
if st.session_state.selected_discussion:
    loaded_history = load_discussion_history(st.session_state.selected_discussion)
    st.session_state.discussion_history = loaded_history

# --- Removed background_markdown function from here ---

def main() -> None:
    """Main function for the Streamlit app."""
    # --- Remove the duplicate calls ---
    column1, column2 = st.columns([3, 2])
    with column1:
        # Load a random background image with a unique cache key
        selected_background = load_background_images("TeamForgeAI/files/backgrounds", cache_key=random.random()) 

        # Display the virtual office with the selected background
        st.markdown('<div class="virtual-office-column">', unsafe_allow_html=True)
        with open(selected_background, "rb") as file:
            image_data = file.read()
            background_image_b64 = base64.b64encode(image_data).decode("utf-8")
        display_virtual_office(background_image_b64)
        st.markdown('</div>', unsafe_allow_html=True)

    with column2:
        display_user_request_input()
        display_rephrased_request()
        display_user_input()

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
            st.write("Last Request:", key="last_request_label")
            st.write(st.session_state.last_request, key="last_request_value")

        discussions = list_discussions()
        selected_discussion = st.selectbox("Load Previous Discussion", [""] + discussions, index=0, key="discussion_selectbox")
        if selected_discussion:
            st.session_state.selected_discussion = selected_discussion
            st.session_state.discussion_history = load_discussion_history(selected_discussion)
        display_download_button()

        # --- Removed unused generate_and_display_image call ---

    # Save discussion history whenever it changes
    if st.session_state.discussion_history:
        save_discussion_history(st.session_state.discussion_history, st.session_state.selected_discussion or f"discussion_{datetime.now().strftime('%Y%m%d_%H%M%S')}")

    if st.session_state.trigger_rerun:
        st.session_state.trigger_rerun = False  # Reset the flag
        st.rerun()  # Now call rerun

if __name__ == "__main__":
    main()
