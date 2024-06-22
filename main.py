# TeamForgeAI/main.py
import streamlit as st
from streamlit.components.v1 import html
st.set_page_config(layout="wide")
import os

# Function to load other apps as plugins
import sys  # Import the sys module

def load_plugin(plugin_name):
    plugin_dir = os.path.join(os.path.dirname(__file__), 'plugins', plugin_name)
    plugin_path = os.path.join(plugin_dir, 'main.py')
    if not os.path.exists(plugin_path):
        st.error(f"Plugin {plugin_name} not found at {plugin_path}")
        return

    # Add the plugin's directory to the Python path
    sys.path.append(plugin_dir)

    with open(plugin_path, encoding='utf-8') as f:
        code = compile(f.read(), plugin_path, 'exec')
        exec(code, globals())

    # Optionally remove the plugin's directory from the Python path
    # sys.path.remove(plugin_dir)
    
# Initialize current_app in session state if not present
if "current_app" not in st.session_state:
    st.session_state.current_app = "TeamForgeAI"

# Sidebar for navigation
with st.sidebar:
    # Use st.markdown for button styling
    st.markdown("""
    <style>
    div.stButton > button {
        width: 100%;
        background-color: transparent;
    }
    /* Style the active button to be orange */
    div.stButton > button:focus
    {
        background-color: orange!important;
        color: white!important;
    }
    div.stButton > button:hover
    {
        background-color: transparent!important;
    }
    </style>
    """, unsafe_allow_html=True)

    # Create two columns for the buttons
    col1, col2 = st.columns(2)

    # TeamForgeAI button
    with col1:
        teamforgeai_active = st.session_state.current_app == "TeamForgeAI"
        if st.button("TeamForgeAI", key="teamforgeai_button", type="primary" if teamforgeai_active else "secondary"):
            st.session_state.current_app = "TeamForgeAI"

    # Ollama Workbench button
    with col2:
        ollama_active = st.session_state.current_app == "Ollama Workbench"
        if st.button("Ollama Workbench", key="ollama_button", type="primary" if ollama_active else "secondary"):
            st.session_state.current_app = "Ollama Workbench"

# Define app here, outside the conditional blocks
app = st.session_state.current_app

# Load the selected app
if st.session_state.current_app == "TeamForgeAI":
    # Load the main TeamForgeAI app
    import config
    from datetime import datetime
    import base64
    import random
    import requests
    import time
    import json

    from agent_display import display_agents
    from ui.discussion import display_discussion_and_whiteboard, update_discussion_and_whiteboard
    from ui.inputs import display_user_input, display_rephrased_request, display_user_request_input
    from ui.utils import display_download_button, list_discussions, load_discussion_history, save_discussion_history, cleanup_old_files, handle_begin
    from ui.virtual_office import display_virtual_office, load_background_images

    from current_project import CurrentProject
    from skills.update_project_status import update_project_status
    from skills.summarize_project_status import summarize_project_status
    from autogen.agentchat import ConversableAgent, GroupChat, GroupChatManager  # Import for automated group chat
    from autogen.agentchat.contrib.capabilities.teachability import Teachability  # Import Teachability

    from ollama_llm import OllamaLLM  # Import OllamaLLM from ollama_llm.py
    from agent_creation import create_autogen_agent # Import from agent_creation.py

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
    if "enable_chat_manager_memory" not in st.session_state:
        st.session_state.enable_chat_manager_memory = True  # Chat Manager memory is ON by default
    if "chat_manager_db_path" not in st.session_state:
        st.session_state.chat_manager_db_path = "./db/group_chat_manager"
    if "auto_mode" not in st.session_state:
        st.session_state.auto_mode = False  # Auto mode is OFF by default

    # Ensure agents_data is initialized
    if "agents_data" not in st.session_state:
        st.session_state.agents_data = []

    # Load selected discussion into session state
    if st.session_state.selected_discussion:
        loaded_history = load_discussion_history(st.session_state.selected_discussion)
        st.session_state.discussion_history = loaded_history

    class OllamaGroupChatManager(GroupChatManager):
        """A GroupChatManager that uses OllamaLLM for text generation."""

        def __init__(self, groupchat, **kwargs):  # Remove the ollama_llm parameter
            super().__init__(groupchat, **kwargs)
            self.current_speaker_index = 0  # Initialize current speaker index

        def generate_reply(self, messages, sender, config=None):
            """Overrides the generate_reply method to use the speaker's OllamaLLM."""
            current_speaker = next(agent for agent in self.groupchat.agents if agent.name == sender)
            prompt = self._construct_prompt(messages, sender, config)
            reply = current_speaker.ollama_llm.generate_text(prompt, temperature=current_speaker.ollama_llm.temperature)
            return reply
        
        def _construct_prompt(self, messages, sender, config):
            """Constructs the prompt for the LLM."""
            # Implement the logic to construct the prompt from the messages and sender
            # This is a placeholder implementation and should be customized as needed
            return "\n".join([msg['content'] for msg in messages])

        def select_next_speaker(self, groupchat):
            """Selects the next speaker in a round-robin fashion."""
            self.current_speaker_index = (self.current_speaker_index + 1) % len(groupchat.agents)
            return groupchat.agents[self.current_speaker_index]

        def initiate_chat_round_robin(self, initial_message):
            """Initiates the chat and ensures all agents get a turn to speak."""
            messages = [{'content': initial_message, 'sender': 'User'}]
            for _ in range(len(self.groupchat.agents) * 2):  # Adjust multiplier for more rounds
                current_speaker = self.select_next_speaker(self.groupchat)
                reply = self.generate_reply(messages, current_speaker.name)
                messages.append({'content': reply, 'sender': current_speaker.name})
                self.groupchat.messages.append({'sender': current_speaker.name, 'content': reply})
                update_discussion_and_whiteboard(current_speaker.name, reply, "")  # Update discussion history

    def main() -> None:
        """Main function for the Streamlit app."""

        # Load agents from files
        load_agents_from_files()

        # Apply CSS for 100% width buttons in the sidebar
        st.sidebar.markdown("""
        <style>
        div.stButton > button {
            width: 100%;
        }
        </style>
        """, unsafe_allow_html=True)
        
        column1, column2 = st.columns([2, 3])  # Swapped the column widths to move office to the right
        with column1:
            display_user_request_input()
            display_rephrased_request()
            display_user_input()

            # Add a button to toggle auto mode
            if st.button("Toggle Auto Mode"):
                st.session_state.auto_mode = not st.session_state.auto_mode
                if st.session_state.auto_mode:
                    st.info("Auto Mode is ON. The Chat Manager will now handle agent interactions.")
                    initiate_auto_mode() # Start Auto Mode when button is clicked
                else:
                    st.info("Auto Mode is OFF. You can interact with agents individually.")

        with column2:
            # Load a random background image with a unique cache key
            selected_background = load_background_images("TeamForgeAI/files/backgrounds", cache_key=random.random())

            # Display the virtual office with the selected background
            st.markdown('<div class="virtual-office-column">', unsafe_allow_html=True)
            if selected_background:
                with open(selected_background, "rb") as file:
                    image_data = file.read()
                    background_image_b64 = base64.b64encode(image_data).decode("utf-8")
                display_virtual_office(background_image_b64)
            st.markdown('</div>', unsafe_allow_html=True)

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
            st.experimental_rerun()  # Trigger a rerun of the Streamlit script

    def load_agents_from_files():
        """Loads agents from JSON files in the 'agents' directory."""
        agents_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "files", "agents"))
        if not os.path.exists(agents_dir):
            os.makedirs(agents_dir)
        for filename in os.listdir(agents_dir):
            if filename.endswith(".json"):
                with open(os.path.join(agents_dir, filename), "r") as f:
                    agent_data = json.load(f)
                    # Create and append the agent
                    st.session_state.agents_data.append(agent_data)

    def initiate_auto_mode():
        """Initiates the automated group chat workflow."""
        if st.session_state.agents_data and st.session_state.rephrased_request and st.session_state.current_project:
            # Disable memory for auto mode
            st.session_state.enable_chat_manager_memory = False

            # Create agents from session state, without teachability
            agents = [create_autogen_agent(agent_data) for agent_data in st.session_state.agents_data]

            # Create group chat and manager
            group_chat = GroupChat(agents=agents, messages=[], max_round=10)

            # Create OllamaGroupChatManager instance
            group_chat_manager = OllamaGroupChatManager(groupchat=group_chat)

            # Initiate the chat with the re-engineered prompt
            group_chat_manager.initiate_chat_round_robin(
                st.session_state.rephrased_request  # Use rephrased_request here
            )

            # Turn off auto mode after the chat is complete
            st.session_state.auto_mode = False
            st.session_state.trigger_rerun = True  # Trigger a rerun to display the updated discussion history
        else:
            st.warning("Please make sure you have added agents and entered a user request before enabling Auto Mode.")

    def terminate_auto_mode():
        """Terminates the automated group chat workflow."""
        st.info("Terminating Auto Mode")
        st.session_state.auto_mode = False  # Set auto_mode to False to stop the loop

        # Clear any existing chat state or messages
        st.session_state.agents_data = []
        st.session_state.rephrased_request = ""
        st.session_state.current_project = CurrentProject()  # Reinitialize current_project to prevent AttributeError

        st.experimental_rerun()  # Trigger a rerun of the Streamlit script to apply changes

    if __name__ == "__main__":
        main()

elif app == "Ollama Workbench":
    load_plugin("Ollama_Workbench")
