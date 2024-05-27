# TeamForgeAI/file_utils.py
import json
import os
import re
import random

def sanitize_text(text):
    text = "".join(c for c in text if c.isprintable())
    return text

emoji_list = ["🐶", "🐱", "🐭", "🐹", "🐰", "🦊", "🐻", "🐼", "🐻‍❄️", "🐨", "🐯", "🦁", "🐮", "🐷", "🐸", "🐵", "🐔", "🐧", "🐦", "🐤", "🐣", "🐥", "🦆", "🦅", "🦉", "🦇", "🐺", "🐗", "🐴", "🦄", "🐝", "🐛", "🦋", "🐌", "🐞", "🐜", "🪲", "🪳", "🪰", "🪱", "🐢", "🐍", "🦎", "🦖", "🦕", "🐙", "🦑", "🦐", "🦞", "🦀", "🐡", "🐠", "🐟", "🐬", "🐳", "🐋", "🦈", "🐊", "🐅", "🐆", "🦓", "🦍", "🦧", "🦣", "🐘", "🦏", "🦛", "🐪", "🐫", "🦒", "🦘", "🦬", "🐃", "🐂", "🐄", "🐎", "🐖", "🐏", "🐑", "🦙", "🐐", "🦌", "🦝", "🦡", "🦃", "🦚", "🦜", "🦢", "🦩", "🕊️", "🦤", "🐉", "🐲", "🌵"]

def create_agent_data(expert_name, description, skills=None, tools=None, enable_reading_html=False, ollama_url="http://localhost:11434", temperature=0.10, model="mistral:7b-instruct-v0.2-q8_0"): # Add agent-specific settings and defaults
    # Format the expert_name
    formatted_expert_name = sanitize_text(expert_name)
    formatted_expert_name = formatted_expert_name.lower().replace(" ", "_")
    # Sanitize the description
    sanitized_description = sanitize_text(description)
    # Sanitize the skills and tools
    sanitized_skills = [sanitize_text(skill) for skill in skills] if skills else []
    sanitized_tools = [sanitize_text(tool) for tool in tools] if tools else []
    # Create the agent data
    agent_data = {
        "type": "assistant",
        "config": {
            "name": expert_name,  # Use the original expert_name here
            "llm_config": {
                "config_list": [
                    {
                        "model": model  # Default to Llama3
                    }
                ],
                "temperature": temperature, # Use agent-specific temperature or default
                "timeout": 600,
                "cache_seed": 42,
            },
            "human_input_mode": "NEVER",
            "max_consecutive_auto_reply": 8,
            "system_message": f"You are a helpful assistant that can act as {expert_name} who {sanitized_description}.",
        },
        "description": description,  # Use the original description here
        "emoji": random.choice(emoji_list), # Add a random emoji
        "skills": sanitized_skills,
        "tools": sanitized_tools,
        "enable_reading_html": enable_reading_html,
        "ollama_url": ollama_url, # Add agent-specific settings
        "temperature": temperature,
        "model": model,
    }
    crewai_agent_data = {
        "name": expert_name,
        "description": description,
        "skills": sanitized_skills,
        "tools": sanitized_tools,
        "verbose": True,
        "allow_delegation": True,
    }
    return agent_data, crewai_agent_data


def create_workflow_data(workflow):
    # Sanitize the workflow name
    sanitized_workflow_name = sanitize_text(workflow["name"])
    sanitized_workflow_name = sanitized_workflow_name.lower().replace(" ", "_")

    return workflow


def load_skills():
    """Loads skills from the 'skills' directory."""
    skills_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "skills"))
    skill_functions = {}
    for filename in os.listdir(skills_dir):
        if filename.endswith(".py"):  # Load Python files
            module_name = filename[:-3]  # Remove '.py' extension
            try:
                # Import the module dynamically
                module = __import__(f"skills.{module_name}", fromlist=[module_name])
                # Get the function from the module (assuming the function name is the same as the module name)
                skill_function = getattr(module, module_name)
                skill_functions[module_name] = skill_function
            except ImportError as e:
                print(f"Error importing skill from {filename}: {e}")
    return skill_functions


def save_agent_to_json(agent_data, filename="agents/agent.json"):
    """Saves agent data to a JSON file."""
    os.makedirs(os.path.dirname(filename), exist_ok=True)  # Ensure directory exists
    with open(filename, "w") as f:
        json.dump(agent_data, f, indent=4)


def load_agents_from_json(directory='agents/'):
    """Loads agents from JSON files in the specified directory."""
    agents = []
    agents_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), directory))
    for filename in os.listdir(agents_dir):
        if filename.endswith('.json'):
            filepath = os.path.join(agents_dir, filename)
            try:
                with open(filepath, 'r') as f:
                    agent_data = json.load(f)
                    agents.append(agent_data)
            except Exception as e:
                print(f"Error loading agent from {filepath}: {e}")
    return agents
