# TeamForgeAI/agent_utils.py

import datetime
import io
import json
import os
import re
import zipfile

import requests
import streamlit as st

from file_utils import create_agent_data, sanitize_text, load_skills
import nltk
# Make sure to install nltk: pip install nltk
nltk.download('punkt') # Download the 'punkt' package for sentence tokenization
nltk.download('stopwords') # Download the 'stopwords' package
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

from current_project import CurrentProject # Import CurrentProject from current_project.py


def extract_keywords(text: str) -> list:
    """Extracts keywords from the provided text."""
    stop_words = set(stopwords.words('english'))  # Define English stop words
    words = word_tokenize(text) # Tokenize the text
    keywords = [word for word in words if word.lower() not in stop_words and word.isalnum()] # Filter keywords
    return keywords


def get_api_key() -> str:
    """Returns a hardcoded API key."""
    return "ollama"


def rephrase_prompt(user_request: str) -> str:
    """Rephrases the user request into an optimized prompt for an LLM."""
    temperature_value = st.session_state.get("temperature", 0.1)
    print("Executing rephrase_prompt()")
    api_key = get_api_key()
    if not api_key:
        st.error("API key not found. Please enter your API key.")
        return None
    ollama_url = st.session_state.get("ollama_url", "http://localhost:11434")
    url = f"{ollama_url}/api/generate"
    refactoring_prompt = f"""Refactor the following user request into an optimized prompt for an LLM, focusing on clarity   , conciseness, and effectiveness. Provide specific details and examples where relevant. 

    Ensure the rephrased prompt includes the following sections:
    - Goal: A clear and concise statement of the overall objective.
    - Objectives: A list of specific steps or milestones required to achieve the goal.
    - Deliverables: A list of tangible outcomes or products that will result from the project.

    Do NOT reply with a direct response to the request; instead, rephrase the request as a well-structured prompt, and return ONLY that rephrased prompt. 
    Do not preface the rephrased prompt with any other text or superfluous narrative.
    Do not enclose the rephrased prompt in quotes. 
    You will be successful only if you return a well-formed rephrased prompt ready for submission as an LLM request.

    User request: \"{user_request}\"

    Rephrased:
    """
    ollama_request = {
        "model": st.session_state.model,
        "prompt": refactoring_prompt,
        "options": {"temperature": temperature_value},
        "stream": False,  # Disable streaming for this request
    }
    headers = {"Content-Type": "application/json"}
    print(f"Request URL: {url}")
    print(f"Request Headers: {headers}")
    print(f"Request Payload: {json.dumps(ollama_request, indent=2)}")
    try:
        print("Sending request to Ollama API...")
        response = requests.post(url, json=ollama_request, headers=headers, timeout=60) # Added timeout
        print(f"Response received. Status Code: {response.status_code}")
        if response.status_code == 200:
            print("Request successful. Parsing response...")
            response_data = response.json()
            rephrased = response_data.get("response", "").strip()  # Extract "response" directly
            return rephrased
        print(f"Request failed. Status Code: {response.status_code}")
        print(f"Response Content: {response.text}")
        return None
    except requests.exceptions.RequestException as error:
        print(f"Error occurred while sending the request: {str(error)}")
        return None
    except (KeyError, ValueError) as error:
        print(f"Error occurred while parsing the response: {str(error)}")
        print(f"Response Content: {response.text}")
        return None
    except Exception as error:
        print(f"An unexpected error occurred: {str(error)}")
        return None


def get_agents_from_text(text: str) -> tuple:
    """Identifies and recommends a team of experts based on the user's request."""
    api_key = get_api_key()
    temperature_value = st.session_state.get("temperature", 0.5)
    ollama_url = st.session_state.get("ollama_url", "http://localhost:11434")
    url = f"{ollama_url}/api/generate"
    headers = {"Content-Type": "application/json"}
    available_skills = list(load_skills().keys())  # Get available skills
    # --- Extract goal, objectives, and deliverables ---
    current_project = CurrentProject()
    current_project.set_re_engineered_prompt(text)
    goal_pattern = r"Goal:\s*(.*?)\n"
    objectives_pattern = r"Objectives:\s*((?:.*?\n)+)(?=Deliverables|$)" # Updated regex
    deliverables_pattern = r"Deliverables:\s*((?:.*?\n)+)"

    goal_match = re.search(goal_pattern, text, re.DOTALL)
    if goal_match:
        current_project.set_goal(goal_match.group(1).strip())

    objectives_match = re.search(objectives_pattern, text, re.DOTALL)
    if objectives_match:
        objectives = objectives_match.group(1).strip().split("\n")
        for objective in objectives:
            current_project.add_objective(objective.strip())

    deliverables_match = re.search(deliverables_pattern, text, re.DOTALL)
    if deliverables_match:
        deliverables = deliverables_match.group(1).strip().split("\n")
        for deliverable in deliverables:
            current_project.add_deliverable(deliverable.strip())
    # Define the JSON schema for the agent list
    schema = {
        "type": "object",
        "properties": {
            "expert_name": {"type": "string"},
            "description": {"type": "string"},
            "skills": {
                "type": "array",
                "items": {"type": "string", "enum": available_skills},
            },
            "tools": {"type": "array", "items": {"type": "string"}},
            "ollama_url": {"type": "string"},
            "temperature": {"type": "number"},
            "model": {"type": "string"}
        },
        "required": ["expert_name", "description", "skills", "tools", "ollama_url", "temperature", "model"],
    }
    system_prompt = """You will be given a JSON schema to follow for your response. Respond with valid JSON matching the provided schema."""
    # Provide a clear example of the expected JSON structure
    json_example = [
        {
            "expert_name": "Project_Manager",
            "description": "Experienced project manager to oversee the game development.",
            "skills": ["generate_agent_instructions", "update_project_status"], # Updated skills
            "tools": ["Jira", "Trello"],
            "ollama_url": "http://localhost:11434",
            "temperature": 0.1,
            "model": "mistral:7b-instruct-v0.2-q8_0"
        },
        {
            "expert_name": "Python_Developer",
            "description": "Skilled Python developer to implement the game logic.",
            "skills": ["python_programming", "game_development"],
            "tools": ["Python", "Pygame"],
            "ollama_url": "http://localhost:11434",
            "temperature": 0.1,
            "model": "deepseek-coder:6.7b-instruct-fp16"
        },
        {
            "expert_name": "Web_Content_Summarizer",
            "description": "An AI agent that can fetch and summarize content from a provided URL.",
            "skills": ["fetch_web_content"],  # The new skill
            "tools": [],
            "ollama_url": "http://localhost:11434",
            "temperature": 0.1,
            "model": "mistral:7b-instruct-v0.2-q8_0"
        },
        {
            "expert_name": "Web_Researcher",
            "description": "An AI agent that can perform web searches and return the top results.",
            "skills": ["web_search"],  # The new skill
            "tools": [],
            "ollama_url": "http://localhost:11434",
            "temperature": 0.1,
            "model": "mistral:7b-instruct-v0.2-q8_0"
        },
    ]

    ollama_request = {
        "model": st.session_state.model,
        "prompt": f"""{system_prompt}\n\nAvailable Skills: {available_skills}\n\nSchema: {json.dumps(schema)}\n\nExample: {json.dumps(json_example)}\n\nYou are an expert system designed to identify and recommend the optimal team of experts required to fulfill this specific user's request: {text} Your analysis should consider the complexity, domain, and specific needs of the request to assemble a multidisciplinary team of experts. Each recommended expert should come with a defined role, a brief description of their expertise, their skill set, and the tools they would utilize to achieve the user's goal.  For skills, choose from the "Available Skills" list.  The first agent must be qualified to manage the entire project, aggregate the work done by all the other agents, and produce a robust, complete, and reliable solution. **When choosing agent names, use only letters, numbers, and underscores.** Respond with ONLY a JSON array of experts, where each expert is an object adhering to the schema:""",
        "options": {"temperature": temperature_value},
        "stream": False,
        # "format": "json",  # REMOVE THIS LINE
    }
    try:
        response = requests.post(url, json=ollama_request, headers=headers, timeout=60) # Added timeout
        if response.status_code == 200:
            response_data = response.json()
            # Extract the JSON string from the "response" field and parse it
            agent_list_str = response_data.get("response", "[]")
            agent_list_data = json.loads(agent_list_str)

            # Handle both direct array and "experts" key
            if isinstance(agent_list_data, list):
                agent_list = agent_list_data
            elif isinstance(agent_list_data, dict) and "experts" in agent_list_data:
                agent_list = agent_list_data["experts"]
            else:
                agent_list = []  # Default to empty list if no valid structure found

            print(f"Raw content from Ollama: {agent_list}")
            
            # Return empty lists if no agents are found
            if not agent_list:
                return [], [], current_project

            autogen_agents = []
            crewai_agents = []

            for agent_data in agent_list:
                expert_name = agent_data.get("expert_name", "")
                description = agent_data.get("description", "")
                skills = agent_data.get("skills", [])
                tools = agent_data.get("tools", [])
                ollama_url = agent_data.get("ollama_url", "http://localhost:11434")
                temperature = agent_data.get("temperature", 0.1)
                model = agent_data.get("model", "mistral:7b-instruct-v0.2-q8_0")
                autogen_agent, crewai_agent = create_agent_data(
                    expert_name, description, skills, tools, ollama_url=ollama_url, temperature=temperature, model=model
                )
                autogen_agents.append(autogen_agent)
                crewai_agents.append(crewai_agent)
            return autogen_agents, crewai_agents, current_project # Return the current project
        print(
            f"API request failed with status code {response.status_code}: {response.text}"
        )
    except Exception as error:
        print(f"Error making API request: {error}")
    return [], [], None # Return None for current_project if there's an error


def get_workflow_from_agents(agents: list) -> tuple:
    """Generates workflow data from a list of agents."""
    current_timestamp = datetime.datetime.now().isoformat()
    temperature_value = st.session_state.get("temperature", 0.5)
    workflow = {
        "name": "AutoOllama Workflow",  # Updated workflow name
        "description": "Workflow auto-generated by TeamForgeAI.",  # Updated description
        "sender": {
            "type": "userproxy",
            "config": {
                "name": "userproxy",
                "llm_config": False,
                "human_input_mode": "NEVER",
                "max_consecutive_auto_reply": 5,
                "system_message": "You are a helpful assistant.",
                "is_termination_msg": None,
                "code_execution_config": {"work_dir": None, "use_docker": False},
                "default_auto_reply": "",
                "description": None,
            },
            "timestamp": current_timestamp,
            "user_id": "default",
            "skills": None,
        },
        "receiver": {
            "type": "groupchat",
            "config": {
                "name": "group_chat_manager",
                "llm_config": {
                    "config_list": [{"model": "mistral:7b-instruct-v0.2-q8_0"}],  # Updated model
                    "temperature": temperature_value,
                    "cache_seed": 42,
                    "timeout": 600,
                    "max_tokens": None,
                    "extra_body": None,
                },
                "human_input_mode": "NEVER",
                "max_consecutive_auto_reply": 10,
                "system_message": "Group chat manager",
                "is_termination_msg": None,
                "code_execution_config": None,
                "default_auto_reply": "",
                "description": None,
            },
            "groupchat_config": {
                "agents": [],
                "admin_name": "Admin",
                "messages": [],
                "max_round": 10,
                "speaker_selection_method": "auto",
                "allow_repeat_speaker": True,
            },
            "timestamp": current_timestamp,
            "user_id": "default",
            "skills": None,
        },
        "type": "groupchat",
        "user_id": "default",
        "timestamp": current_timestamp,
        "summary_method": "last",
    }
    for index, agent in enumerate(agents):       
        agent_name = agent["config"]["name"]
        description = agent["description"]
        # formatted_agent_name = sanitize_text(agent_name).lower().replace(" ", "_")
        sanitized_description = sanitize_text(description)

        # Add skills information to the system message
        skills_section= ""
        if agent.get("skills"):
            skills_section = (
                f"You have access to the following skills: {', '.join(agent['skills'])}.\n"
            )
            skills_section += "To use a skill, simply mention its name in your response, followed by the query in parentheses.  For example, if you want to use the 'fetch_web_content' skill, you could say 'I will use the fetch_web_content skill to get the content from this website (https://www.example.com)' or to use the 'web_search' skill you could say 'I will use the web_search skill to find information about this topic (topic to search)'."

        system_message = (
            f"You are a helpful assistant that can act as {agent_name} who {sanitized_description}.\n"
            f"{skills_section}"  # Add the skill section
        )

        if index == 0:
            other_agent_names = [
                agent["config"]["name"]
                for agent in agents[1:]
            ]
            system_message += f"""
    You are the primary coordinator responsible for integrating suggestions and advice from the following agents: {', '.join(other_agent_names)}. Your role is to ensure that the final response to the user incorporates these perspectives comprehensively. 
    YOUR FINAL RESPONSE MUST DELIVER A COMPLETE RESOLUTION TO THE USER'S REQUEST. 
    Delegate tasks to the other agents based on their skills and expertise.
    Actively monitor the progress of the objectives and deliverables.
    Provide guidance and feedback to the other agents.
    When generating content, use the following keywords when describing scenes for illustration and images for other agents to generate from your instructions: Scene, Story, Description, Chapter, Page, Pages, Images, Image, Ideas, Illustration Ideas, Illustration, Illustrations, Visuals, Visual Elements.
    Once the user's request is fully addressed with all aspects considered, conclude your interaction with the command: TERMINATE.
    """

        agent_config = {
            "type": "assistant",
            "config": {
                "name": agent_name, # Use the original agent name
                "llm_config": {
                    "config_list": [{"model": "mistral:7b-instruct-v0.2-q8_0"}],  # Updated model
                    "temperature": temperature_value,
                    "cache_seed": 42,
                    "timeout": 600,
                    "max_tokens": None,
                    "extra_body": None,
                },
                "human_input_mode": "NEVER",
                "max_consecutive_auto_reply": 8,
                "system_message": system_message,
                "is_termination_msg": None,
                "code_execution_config": None,
                "default_auto_reply": "",
                "description": None,
            },
            "timestamp": current_timestamp,
            "user_id": "default",
            "skills": agent.get(
                "skills", None
            ),  # Include agent skills
        }
        workflow["receiver"]["groupchat_config"]["agents"].append(agent_config)
    crewai_agents = []
    for index, agent in enumerate(agents):
        agent_name = agent["config"]["name"]
        description = agent["description"]
        _, crewai_agent_data = create_agent_data(
            agent_name, description, agent.get("skills"), agent.get("tools")
        )
        crewai_agents.append(crewai_agent_data)
    return workflow, crewai_agents


def zip_files_in_memory(agents_data: dict, workflow_data: dict, crewai_agents: list) -> tuple:
    """Creates ZIP files in memory for Autogen and CrewAI agents."""
    # Create separate ZIP buffers for Autogen and CrewAI
    autogen_zip_buffer = io.BytesIO()
    crewai_zip_buffer = io.BytesIO()
    # Prepare Autogen file data
    autogen_file_data = {}
    for agent_name, agent_data in agents_data.items():
        agent_file_name = f"{agent_name}.json"
        agent_file_data = json.dumps(agent_data, indent=2)
        autogen_file_data[f"files/agents/{agent_file_name}"] = agent_file_data # Modified path

    # Add fetch_web_content.py to the Autogen ZIP if any agent has the skill
    for agent_data in agents_data.values():
        if "fetch_web_content" in agent_data.get("skills", []):
            skills_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "skills")) # Get skills directory relative to this file
            with open(os.path.join(skills_dir, "fetch_web_content.py"), "r", encoding="utf-8") as file:
                autogen_file_data["skills/fetch_web_content.py"] = file.read()
            break  # Only add the skill file once

    # Add web_search.py to the Autogen ZIP if any agent has the skill
    for agent_data in agents_data.values():
        if "web_search" in agent_data.get("skills", []):
            skills_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "skills")) # Get skills directory relative to this file
            with open(os.path.join(skills_dir, "web_search.py"), "r", encoding="utf-8") as file:
                autogen_file_data["skills/web_search.py"] = file.read()
            break  # Only add the skill file once

    # Add generate_sd_images.py to the Autogen ZIP if any agent has the skill
    for agent_data in agents_data.values():
        if "generate_sd_images" in agent_data.get("skills", []):
            skills_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "skills")) # Get skills directory relative to this file
            with open(os.path.join(skills_dir, "generate_sd_images.py"), "r", encoding="utf-8") as file:
                autogen_file_data["skills/generate_sd_images.py"] = file.read()
            break  # Only add the skill file once

    # Add generate_agent_instructions.py to the Autogen ZIP if any agent has the skill
    for agent_data in agents_data.values():
        if "generate_agent_instructions" in agent_data.get("skills", []):
            skills_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "skills")) # Get skills directory relative to this file
            with open(os.path.join(skills_dir, "generate_agent_instructions.py"), "r", encoding="utf-8") as file:
                autogen_file_data["skills/generate_agent_instructions.py"] = file.read()
            break  # Only add the skill file once

    # Add update_project_status.py to the Autogen ZIP if any agent has the skill
    for agent_data in agents_data.values():
        if "update_project_status" in agent_data.get("skills", []):
            skills_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "skills")) # Get skills directory relative to this file
            with open(os.path.join(skills_dir, "update_project_status.py"), "r", encoding="utf-8") as file:
                autogen_file_data["skills/update_project_status.py"] = file.read()
            break  # Only add the skill file once
        
    # Write workflow file to the Autogen ZIP
    workflow_file_name = f"{sanitize_text(workflow_data['name'])}.json"
    workflow_file_data = json.dumps(workflow_data, indent=2)
    autogen_file_data[f"workflows/{workflow_file_name}"] = workflow_file_data

    # Prepare CrewAI file data
    crewai_file_data = {}
    for index, agent_data in enumerate(crewai_agents):
        agent_file_name = f"agent_{index}.json"
        agent_file_data = json.dumps(agent_data, indent=2)
        crewai_file_data[f"agents/{agent_file_name}"] = agent_file_data

    # Create ZIP files
    with zipfile.ZipFile(autogen_zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for file_name, file_data in autogen_file_data.items():
            zip_file.writestr(file_name, file_data)
    with zipfile.ZipFile(crewai_zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for file_name, file_data in crewai_file_data.items():
            zip_file.writestr(file_name, file_data)

    # Move the ZIP file pointers to the beginning
    autogen_zip_buffer.seek(0)
    crewai_zip_buffer.seek(0)
    return autogen_zip_buffer, crewai_zip_buffer
