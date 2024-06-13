# TeamForgeAI/file_utils.py

import json
import os
import random

def sanitize_text(text: str) -> str:
    """Sanitizes the provided text by removing non-printable characters."""
    return "".join(c for c in text if c.isprintable())

emoji_list = ["🐶", "🐱", "🐭", "🐹", "🐰", "🦊", "🐻", "🐼", "🐻‍❄️", "🐨", "🐯", "🦁", "🐮", "🐷", "🐸", "🐵", "🐔", "🐧", "🐦", "🐤", "🐣", "🐥", "🦆", "🦅", "🦉", "🦇", "🐺", "🐗", "🐴", "🦄", "🐝", "🐛", "🦋", "🐌", "🐞", "🐜", "🪲", "🪳", "🪰", "🪱", "🐢", "🐍", "🦎", "🦖", "🦕", "🐙", "🦑", "🦐", "🦞", "🦀", "🐡", "🐠", "🐟", "🐬", "🐳", "🐋", "🦈", "🐊", "🐅", "🐆", "🦓", "🦍", "🦧", "🦣", "🐘", "🦏", "🦛", "🐪", "🐫", "🦒", "🦘", "🦬", "🐃", "🐂", "🐄", "🐎", "🐖", "🐏", "🐑", "🦙", "🐐", "🦌", "🦝", "🦡", "🦃", "🦚", "🦜", "🦢", "🦩", "🕊️", "🦤", "🐉", "🐲", "🌵"]

def create_agent_data(expert_name: str, description: str, skills: list = None, tools: list = None, enable_reading_html: bool = False, ollama_url: str = "http://localhost:11434", temperature: float = 0.10, model: str = "mistral:instruct", db_path: str = None, enable_memory: bool = False) -> tuple:
    """
    Creates agent data for both AutoGen and CrewAI agents.

    Args:
        expert_name (str): The name of the expert.
        description (str): A description of the expert.
        skills (list, optional): A list of skills the expert possesses. Defaults to None.
        tools (list, optional): A list of tools the expert uses. Defaults to None.
        enable_reading_html (bool, optional): Whether the agent can read HTML. Defaults to False.
        ollama_url (str, optional): The URL of the Ollama endpoint. Defaults to "http://localhost:11434".
        temperature (float, optional): The temperature for the language model. Defaults to 0.10.
        model (str, optional): The name of the language model. Defaults to "mistral:instruct".
        db_path (str, optional): The path to the agent's database. Defaults to None.
        enable_memory (bool, optional): Whether to enable memory for the agent. Defaults to False.

    Returns:
        tuple: A tuple containing the AutoGen agent data and the CrewAI agent data.
    """
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
            "db_path": db_path,
            "enable_memory": enable_memory
        },
        "description": description,  # Use the original description here
        "emoji": random.choice(emoji_list), # Add a random emoji
        "skills": sanitized_skills,
        "tools": sanitized_tools,
        "enable_reading_html": enable_reading_html,
        "ollama_url": ollama_url, # Add agent-specific settings
        "temperature": temperature,
        "model": model,
        "skill": sanitized_skills[0] if sanitized_skills else None,  # Add the first skill to the "skill" field
        "db_path": db_path,
        "enable_memory": enable_memory
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

def create_workflow_data(workflow: dict) -> dict:
    """
    Sanitizes the workflow name by removing special characters and replacing spaces with underscores.

    Args:
        workflow (dict): The workflow data.

    Returns:
        dict: The workflow data with a sanitized name.
    """
    # Sanitize the workflow name
    sanitized_workflow_name = sanitize_text(workflow["name"])
    sanitized_workflow_name = sanitized_workflow_name.lower().replace(" ", "_")
    workflow["name"] = sanitized_workflow_name
    return workflow

def load_skills() -> dict:
    """Loads skill functions from Python files in the 'skills' directory."""
    skills_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "skills"))
    skill_functions = {}
    for filename in os.listdir(skills_dir):
        if filename.endswith(".py") and filename != "project_management.py":  # Load Python files, exclude project_management.py
            module_name = filename[:-3]  # Remove '.py' extension
            try:
                # Import the module dynamically
                module = __import__(f"skills.{module_name}", fromlist=[module_name])
                # Get the function from the module (assuming the function name is the same as the module name)
                skill_function = getattr(module, module_name)
                skill_functions[module_name] = skill_function
            except ImportError as error:
                print(f"Error importing skill from {filename}: {error}")
    return skill_functions

def save_agent_to_json(agent_data: dict, filename: str) -> None:
    """Saves agent data to a JSON file."""
    # Get the absolute path to the TeamForgeAI directory
    teamforgeai_dir = os.path.dirname(os.path.dirname(__file__))
    # Construct the absolute path to the filename
    absolute_filename = os.path.join(teamforgeai_dir, filename)
    os.makedirs(os.path.dirname(absolute_filename), exist_ok=True)  # Ensure directory exists
    with open(absolute_filename, "w", encoding="utf-8") as file:
        json.dump(agent_data, file, indent=4)

def load_agents_from_json(directory: str) -> list:
    """Loads agents from JSON files in the specified directory."""
    # Get the absolute path to the TeamForgeAI directory
    teamforgeai_dir = os.path.dirname(os.path.dirname(__file__))
    # Construct the absolute path to the directory
    absolute_directory = os.path.join(teamforgeai_dir, directory)
    agents = []
    if not os.path.exists(absolute_directory):
        os.makedirs(absolute_directory) # Create the directory if it doesn't exist
    for filename in os.listdir(absolute_directory):
        if filename.endswith('.json'):
            filepath = os.path.join(absolute_directory, filename)
            try:
                with open(filepath, 'r', encoding="utf-8") as file:
                    agent_data = json.load(file)
                    agents.append(agent_data)
            except Exception as error:
                print(f"Error loading agent from {filepath}: {error}")
    return agents
