import os
import streamlit as st
from agent_management import display_agents
from ui_utils import (
    get_api_key,
    display_discussion_and_whiteboard,
    display_download_button,
    display_user_input,
    display_rephrased_request,
    display_reset_and_upload_buttons,
    display_user_request_input,
    rephrase_prompt,
    get_agents_from_text,
    extract_code_from_response,
    get_workflow_from_agents,
)

# Set up the page to use a wide layout
st.set_page_config(layout="wide")

def main():
    # Initialize session state variables if they are not already present
    if 'trigger_rerun' not in st.session_state:
        st.session_state.trigger_rerun = False
    if 'whiteboard' not in st.session_state:
        st.session_state.whiteboard = ""
    if 'last_comment' not in st.session_state:
        st.session_state.last_comment = ""
    if 'discussion_history' not in st.session_state:
        st.session_state.discussion_history = ""
    if 'rephrased_request' not in st.session_state:
        st.session_state.rephrased_request = ""
    if 'need_rerun' not in st.session_state:
        st.session_state.need_rerun = False
        
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
            padding: 20px !important;
            border-radius: 5px !important;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1) !important;
        }

        .sidebar .st-emotion-cache-k7vsyb h1 {
            font-size: 12px !important;
            font-weight: bold !important;
            color: #007bff !important;
        }

        .sidebar h2 {
            font-size: 16px !important;
            color: #666666 !important;
        }

        .sidebar .stButton button {
            display: block !important;
            width: 100% !important;
            padding: 10px !important;
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

        .main .stButton button {
            padding: 10px 20px !important;
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

        .main h1 {
            font-size: 32px !important;
            font-weight: bold !important;
            color: #007bff !important;
        }

        /* Model selection styles */
        .main .stSelectbox select {
            width: 100% !important;
            padding: 10px !important;
            border: 1px solid #cccccc !important;
            border-radius: 5px !important;
        }

        /* Error message styles */
        .main .stAlert {
            color: #dc3545 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    model_token_limits = {
        "mistral:7b-instruct-v0.2-q8_0": 8192,
        "deepseek-coder:6.7b-instruct": 8192,
        "deepseek-coder:6.7b-instruct-fp16": 8192,
        "dolphin-llama3:8b-v2.9-fp16": 8192,
        "gemma:2b-instruct": 8192,
        "gemma:2b-instruct-fp16": 8192,
        "llama2:13b-chat-q8_0": 8192,
        "llama3:8b": 8192,
        "llama3:latest": 8192,
        "llama3:8b-instruct-fp16": 8192,
        "llama3-chatqa:8b-v1.5-fp16": 8192,
        "llama3-gradient:8b-instruct-1048k-fp16": 8192,
        "llava-phi3:3.8b-mini-fp16": 8192,
        "mistral:7b-instruct-v0.2-fp16": 8192,
        "nous-hermes2:10.7b-solar-fp16": 8192,
        "open-orca-platypus2:13b-q8_0": 8192,
        "openhermes:7b-mistral-v2.5-fp16": 8192,
        "phi3:3.8b-mini-instruct-4k-fp16": 8192,
        "samantha-mistral:7b-instruct-fp16": 8192
    }

    col1, col2, col3 = st.columns([2, 5, 3])
    with col1:
        st.title("AutoOllama")
        st.text_input(
            "Ollama URL",
            value=st.session_state.get("ollama_url", "http://localhost:11434"),
            key="ollama_url",
        )    
    with col3:
        selected_model = st.selectbox(
            "Select Model",
            options=list(model_token_limits.keys()),
            index=0,
            key="model_selection",
        )
        st.session_state.model = selected_model
        st.session_state.max_tokens = model_token_limits[selected_model]
        temperature = st.slider(
            "Set Temperature",
            min_value=0.0,
            max_value=1.0,
            value=st.session_state.get("temperature", 0.1),
            step=0.01,
            key="temperature",
        )

    

    with st.sidebar:
        display_agents()

    with st.container():
        display_user_request_input()
        display_rephrased_request()
        display_discussion_and_whiteboard()
        display_user_input()
        display_reset_and_upload_buttons()

    display_download_button()

    # At a strategic point, check if a rerun is needed
    if st.session_state.trigger_rerun:
        st.session_state.trigger_rerun = False  # Reset the flag
        st.experimental_rerun()  # Now call rerun

if __name__ == "__main__":
    main()