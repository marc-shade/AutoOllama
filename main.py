# TeamForgeAI/main.py
# Import the configuration first
import config

import os
from datetime import datetime
import base64
import streamlit as st
import random
import requests
import time
import json

# Set up the page to use a wide layout
st.set_page_config(layout="wide")

from agent_display import display_agents
from ui.discussion import display_discussion_and_whiteboard, update_discussion_and_whiteboard
from ui.inputs import display_user_input, display_rephrased_request, display_user_request_input
from ui.utils import display_download_button, list_discussions, load_discussion_history, save_discussion_history, cleanup_old_files, handle_begin
from ui.virtual_office import display_virtual_office, load_background_images

from current_project import CurrentProject
from skills.update_project_status import update_project_status
from skills.summarize_project_status import summarize_project_status
from autogen.agentchat import ConversableAgent, GroupChat, GroupChatManager # Import for automated group chat


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
    st.session_state.enable_chat_manager_memory = True # Chat Manager memory is ON by default
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

class OllamaLLM:
    """A custom LLM wrapper for Ollama."""

    def __init__(self, base_url="http://localhost:11434", api_key=None, model="mistral:instruct", temperature=0.7):
        self.base_url = base_url
        self.api_key = api_key
        self.model = model
        self.temperature = temperature  # Set default temperature here

    def generate_text(self, prompt, temperature=None, max_tokens=512):
        """Generates text using the Ollama API."""
        url = f"{self.base_url}/api/generate"
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        data = {
            "model": self.model,
            "prompt": prompt,
            "options": {
                "temperature": temperature if temperature is not None else self.temperature, # Use provided temperature or default
                "max_tokens": max_tokens,
            },
        }
        response = requests.post(url, headers=headers, json=data, stream=True)
        
        try:
            responses = []
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8').strip()
                    responses.append(json.loads(decoded_line).get("response", ""))
            return "".join(responses)
        except ValueError as e:
            print(f"DEBUG: JSON decode error - {e}")
            print(f"DEBUG: API response text - {responses}")
            raise
        except Exception as e:
            print(f"DEBUG: Unexpected error - {e}")
            raise

class OllamaConversableAgent(ConversableAgent):
    """A ConversableAgent that uses OllamaLLM for text generation."""

    def __init__(self, name, ollama_llm, system_message=None, **kwargs):
        super().__init__(name=name, system_message=system_message, **kwargs)
        self.ollama_llm = ollama_llm

    def generate_reply(self, messages, sender, config=None):
        """Overrides the generate_reply method to use OllamaLLM."""
        prompt = self._construct_prompt(messages, sender, config)
        reply = self.ollama_llm.generate_text(prompt, temperature=self.ollama_llm.temperature)
        return reply

    def _construct_prompt(self, messages, sender, config):
        """Constructs the prompt for the LLM."""
        return "\n".join([msg['content'] for msg in messages])

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
    
    column1, column2 = st.columns([3, 2])
    with column1:
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

    with column2:
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
                terminate_auto_mode() # Stop Auto Mode when button is clicked again

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
                st.session_state.agents_data.append(agent_data)

def create_autogen_agent(agent_data: dict):
    """Creates an AutoGen ConversableAgent from agent data."""
    from autogen.agentchat import ConversableAgent  # Correct import
    from autogen.agentchat.contrib.capabilities.teachability import Teachability

    # Create OllamaLLM instance for the agent
    ollama_llm = OllamaLLM(
        base_url=agent_data["ollama_url"],
        model=agent_data["model"],
        api_key=agent_data.get("api_key"),
        temperature=agent_data.get("temperature", 0.7)  # Use temperature from agent_data or default to 0.7
    )

    agent = OllamaConversableAgent(
        name=agent_data["config"]["name"],
        ollama_llm=ollama_llm,
        system_message=agent_data["config"]["system_message"],
        llm_config=False,  # Pass llm_config=False to prevent OpenAIWrapper creation
    )

    # Only enable memory if not in auto mode
    if agent_data.get("enable_memory", False) and not st.session_state.auto_mode:
        teachability = Teachability(path_to_db_dir=agent_data.get("db_path"))
        teachability.add_to_agent(agent)
    return agent

def initiate_auto_mode():
    """Initiates the automated group chat workflow."""
    if st.session_state.agents_data and st.session_state.rephrased_request and st.session_state.current_project:
        # Create agents from session state
        agents = [create_autogen_agent(agent_data) for agent_data in st.session_state.agents_data]

        # Create group chat and manager
        group_chat = GroupChat(agents=agents, messages=[], max_round=10)

        # Create OllamaGroupChatManager instance without passing a specific OllamaLLM
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
