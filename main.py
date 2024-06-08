# Import the configuration first
import config

import os
from datetime import datetime
import base64
import streamlit as st
import random

# Set up the page to use a wide layout
st.set_page_config(layout="wide")

from agent_display import display_agents
from ui.discussion import display_discussion_and_whiteboard
from ui.inputs import display_user_input, display_rephrased_request, display_user_request_input
from ui.utils import display_download_button, list_discussions, load_discussion_history, save_discussion_history, cleanup_old_files, handle_begin
from ui.virtual_office import display_virtual_office, load_background_images

from current_project import CurrentProject
from skills.update_project_status import update_project_status
from skills.summarize_project_status import summarize_project_status



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
    st.session_state.selected_model = "mistral:instruct"
if "last_request" not in st.session_state:
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
    st.session_state.selected_background = ""
if "current_project" not in st.session_state:
    st.session_state.current_project = CurrentProject()

# Load selected discussion into session state
if st.session_state.selected_discussion:
    loaded_history = load_discussion_history(st.session_state.selected_discussion)
    st.session_state.discussion_history = loaded_history

def main() -> None:
    """Main function for the Streamlit app."""
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

        display_download_button()

    # Save discussion history whenever it changes
    if st.session_state.discussion_history:
        save_discussion_history(st.session_state.discussion_history, st.session_state.selected_discussion or f"discussion_{datetime.now().strftime('%Y%m%d_%H%M%S')}")

    # Call summarize_project_status and display the result
    if st.session_state.discussion_history:
        summary_message = summarize_project_status(discussion_history=st.session_state.discussion_history)
        st.write(summary_message)

    # Call update_project_status and display the result
    if st.session_state.discussion_history:
        status_message = update_project_status(discussion_history=st.session_state.discussion_history)
        # st.write(status_message)  # No need to display the message here, it's added to the discussion history

    if st.session_state.trigger_rerun:
        st.session_state.trigger_rerun = False  # Reset the flag
        st.rerun()  # Now call rerun

if __name__ == "__main__":
    main()
