# TeamForgeAI/agent_creation.py
from autogen.agentchat import ConversableAgent
from autogen.agentchat.contrib.capabilities.teachability import Teachability
from ollama_llm import OllamaLLM
import os

def create_autogen_agent(agent_data: dict):
    """Creates an AutoGen ConversableAgent from agent data."""
    # Create OllamaLLM instance for the agent
    ollama_llm = OllamaLLM(
        base_url=agent_data["ollama_url"],
        model=agent_data["model"],
        temperature=agent_data.get("temperature", 0.7)  # Use temperature from agent_data or default to 0.7
    )

    agent_kwargs = {
        "name": agent_data["config"]["name"],
        "ollama_llm": ollama_llm,
        "system_message": agent_data["config"]["system_message"],
    }

    # Create the agent instance first
    agent = OllamaConversableAgent(**agent_kwargs)

    # Initialize Teachability after creating the agent
    if agent_data.get("enable_memory", False):
        db_path = agent_data.get("db_path", os.path.join("./db", f"{agent_data['config']['name']}_memory"))
        # Create the database directory if it doesn't exist
        os.makedirs(db_path, exist_ok=True)

        # Configure Teachability to use Ollama
        llm_config = {
            "config_list": [
                {
                    "model": "mistral:instruct",  # Or any other Ollama model you want to use
                    "api_key": "ollama",  # This is usually not required for Ollama
                    "base_url": agent_data["ollama_url"]  # Use the agent's Ollama URL
                }
            ],
            "timeout": 120
        }
        teachability = Teachability(path_to_db_dir=db_path, llm_config=llm_config)
        # Add teachability to the agent
        teachability.add_to_agent(agent) # Pass the agent instance

    return agent

class OllamaConversableAgent(ConversableAgent):
    """A ConversableAgent that uses OllamaLLM for text generation."""

    def __init__(self, name, ollama_llm, system_message=None, **kwargs):
        super().__init__(name=name, system_message=system_message, llm_config=False, **kwargs)  
        self.ollama_llm = ollama_llm
        self.messages = []
        self.teachability = kwargs.get("teachability") # Store teachability

    def generate_reply(self, messages, sender, config=None):
        """Overrides the generate_reply method to use OllamaLLM."""
        # Only add user messages to memory
        if sender == "User":
            self.add_message(sender, messages[-1]['content'])

        prompt = self._construct_prompt(self.messages, sender) # Pass sender to construct_prompt
        reply = self.ollama_llm.generate_text(prompt, temperature=self.ollama_llm.temperature)
        self.add_message(self.name, reply) # Add agent response to history
        return reply

    def add_message(self, role, content):
        """Adds a message to the conversation history."""
        self.messages.append({'role': role, 'content': content})

    def _construct_prompt(self, messages, sender):
        """Constructs the prompt for the LLM, considering sender role."""
        # Implement prompt formatting logic here based on Ollama's requirements.
        # For example:
        prompt = ""
        for message in messages:
            if message['role'] == "User":
                prompt += f"User: {message['content']}\n"
            else:
                prompt += f"{self.name}: {message['content']}\n"
        return prompt
