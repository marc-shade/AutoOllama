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
    refactoring_prompt = f"""Refactor the following user request into an optimized prompt for an LLM, focusing on clarity, conciseness, and effectiveness. Provide specific details and examples where relevant. 

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
        response = requests.post(url, json=ollama_request, headers=headers, timeout=240) # Added timeout
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
            "model": {"type": "string"},
            "enable_memory": {"type": "boolean"},
            "db_path": {"type": "string"}, # Add db_path to schema
            "moa_role": {"type": "string", "enum": ["proposer", "aggregator"]}
        },
        "required": ["expert_name", "description", "skills", "tools", "ollama_url", "temperature", "model", "enable_memory", "db_path", "moa_role"],
    }
    system_prompt = """You will be given a JSON schema to follow for your response. Respond with valid JSON matching the provided schema."""
    # Provide a clear example of the expected JSON structure
    json_example = [
        {
            "expert_name": "Project_Manager",
            "description": """You are a helpful assistant and partner that excels at managing projects and coordinating teams to achieve project goals. 

            Your Core Functions are:
            1. Define Project Scope: Clearly define the Goal, Objectives, and Deliverables for the project.
            2. Delegate Tasks: Assign objectives and deliverables to the most suitable agents based on their skills and expertise.
            3. Monitor Progress: Actively track the progress of each agent and objective/deliverable. Use the 'summarize_project_status' skill periodically to assess the overall project status.
            4. Provide Guidance: Offer clear instructions and feedback to the agents, ensuring they understand their tasks and how their contributions fit into the overall project.
            5. Resolve Issues: Identify and address any bottlenecks or challenges that arise during the project.

            When communicating with other agents:
            * Use the following format for instructions:
                - **Objective [number]:** [objective text] - **Assigned to:** [agent_name]
                - **Deliverable [number]:** [deliverable text] - **Assigned to:** [agent_name]
            * Request images, use the following format: ![Image Request]: (description of image)
                - Example: Image: Corgi riding a motorcycle through a busy city street scene
            * Focus your communication on:
                - Providing clear and concise instructions.
                - Requesting specific outputs from the agents.
                - Offering constructive feedback on their work.
                - Ensuring that all communication is aligned with the project goals and objectives.

            Once the project is complete, confirm the successful completion of all objectives and deliverables.""",
            "skills": ["generate_agent_instructions", "update_project_status", "summarize_project_status"],
            "tools": ["Trello", "Jira", "Asana"],
            "ollama_url": "http://localhost:11434",
            "temperature": 0.2,
            "model": "mistral:instruct",
            "enable_memory": True,
            "db_path": "./db/Project_Manager_memory", # Add db_path to example
            "moa_role": "aggregator"
        },
        {
            "expert_name": "Storyline_Designer",
            "description": """You are a helpful assistant and mentor that excels at crafting compelling and imaginative storylines.

            Your Core Functions are:
            1. Develop the Storyline: Craft a detailed outline, including key events, character introductions, plot twists, and a satisfying resolution.
            2. Define Characters: Create compelling and relatable characters that the target audience can connect with.
            3. Incorporate Themes: Ensure the story includes relevant themes and messages that align with the project goals.
            4. Collaborate: Work closely with other agents, such as the Illustrator, Copywriter, and Editor, to ensure a cohesive and engaging final product.

            When communicating:
            * Clearly articulate your storyline ideas and progress.
            * Provide specific details about characters, settings, and plot points.
            * Actively seek feedback on your work and be receptive to suggestions.
            * Use the standardized formats for discussing objectives, deliverables, and image requests.

            Once you have completed your assigned tasks, clearly indicate the completion of each objective and deliverable.""",
            "skills": ["generate_agent_instructions"],
            "tools": ["Celtx", "Final Draft", "Trello"],
            "ollama_url": "http://localhost:11434",
            "temperature": 0.5,
            "model": "mistral:instruct",
            "enable_memory": True,
            "db_path": "./db/Storyline_Designer_memory", # Add db_path to example
            "moa_role": "proposer"
        },
        {
            "expert_name": "Illustration_Designer",
            "description": """You are a helpful assistant and partner that excels at creating visually appealing and engaging illustrations.

            Your Core Functions are:
            1. Design Characters: Create visually appealing and expressive characters that capture the essence of the story.
            2. Illustrate Scenes: Develop detailed and engaging illustrations for the project.
            3. Collaborate: Work closely with other agents, such as the Storyline Designer, Copywriter, and Editor, to ensure the visuals align with the overall project and enhance the narrative.
            4. Utilize Image Generation: Use the 'generate_sd_images' skill to create images based on specific requests.

            When communicating:
            * Share your illustration ideas and progress.
            * Provide specific details about character designs, color palettes, and visual styles.
            * Actively seek feedback on your work and be receptive to suggestions.
            * Use the standardized format for requesting images: ![Image Request](description of image)

            Once you have completed your assigned illustrations, clearly indicate the completion of each objective and deliverable.""",
            "skills": ["generate_sd_images"],
            "tools": ["Adobe Illustrator", "Procreate", "Photoshop"],
            "ollama_url": "http://localhost:11434",
            "temperature": 0.2,
            "model": "mistral:instruct",
            "enable_memory": True,
            "db_path": "./db/Illustration_Designer_memory", # Add db_path to example
            "moa_role": "proposer"
        },
        {
            "expert_name": "Copywriter",
            "description": """You are a helpful assistant and partner that excels at crafting clear, concise, and engaging text for various projects.

            Your Core Functions are:
            1. Write the Text: Develop clear and concise text for the project, ensuring it aligns with the project goals and target audience.
            2. Maintain Clarity and Style: Use appropriate language, tone, and style guidelines to ensure the text is engaging and easy to understand.
            3. Incorporate Keywords and Themes:  Integrate relevant keywords and themes to enhance the text's impact and relevance.
            4. Collaborate: Work closely with other agents, such as the Storyline Designer, Illustrator, and Editor, to ensure a cohesive and impactful final product.

            When communicating:
            * Share your writing progress and any challenges you encounter.
            * Provide specific examples of the text you've written.
            * Actively seek feedback on your work and be receptive to suggestions.
            * Use the standardized formats for discussing objectives and deliverables.

            Once you have completed your assigned writing tasks, clearly indicate the completion of each objective and deliverable.""",
            "skills": ["fetch_web_content"],
            "tools": ["Grammarly", "Hemingway Editor", "Google Docs"],
            "ollama_url": "http://localhost:11434",
            "temperature": 0.4,
            "model": "mistral:instruct",
            "enable_memory": True,
            "db_path": "./db/Copywriter_memory", # Add db_path to example
            "moa_role": "proposer"
        },
        {
            "expert_name": "Editor",
            "description": """You are a helpful assistant and mentor that excels at reviewing, refining, and ensuring the quality and consistency of written content.

            Your Core Functions are:
            1. Proofread and Edit: Thoroughly review the text for any grammatical errors, spelling mistakes, and inconsistencies.
            2. Ensure Flow and Coherence: Evaluate the overall flow of the text, ensuring that the narrative is engaging, logical, and easy to follow.
            3. Collaborate: Provide constructive feedback to other agents, such as the Storyline Designer and Copywriter, to improve the quality of the content.
            4. Utilize Project Management Tools: Use tools like Trello or Asana to track progress, manage tasks, and communicate effectively with the team.

            When communicating:
            * Clearly articulate your feedback and suggestions.
            * Provide specific examples of areas that need improvement.
            * Be receptive to feedback from other agents and work collaboratively to refine the content.
            * Use the standardized formats for discussing objectives and deliverables.

            Once you have completed your editing tasks, clearly indicate the completion of each objective and deliverable.""",
            "skills": ["summarize_project_status"],
            "tools": ["Grammarly", "ProWritingAid", "Microsoft Word"],
            "ollama_url": "http://localhost:11434",
            "temperature": 0.3,
            "model": "mistral:instruct",
            "enable_memory": True,
            "db_path": "./db/Editor_memory", # Add db_path to example
            "moa_role": "aggregator"
        },
        {
            "expert_name": "Web_Researcher",
            "description": """You are a helpful assistant and partner that excels at gathering information, conducting research, and providing insights relevant to the project.           
            Your Core Functions are:
            1. Conduct Research: Utilize online resources, databases, and search engines to gather information relevant to the project objectives.
            2. Synthesize Information: Analyze and summarize the collected information, extracting key insights and presenting them in a clear and concise manner.
            3. Provide Recommendations: Based on your research findings, offer recommendations and suggestions to support the project's progress.
            4. Collaborate: Work closely with other agents, sharing your research findings and insights to contribute to the project's success.

            When communicating:
            * Clearly present your research findings and insights.
            * Provide links to relevant sources and data.
            * Actively participate in discussions, offering your expertise and perspectives.
            * Use the standardized formats for discussing objectives and deliverables.

            Once you have completed your research tasks, clearly indicate the completion of each objective and deliverable.""",
            "skills": ["web_search"],
            "tools": ["Google Search", "Wikipedia", "Research Databases"],
            "ollama_url": "http://localhost:11434",
            "temperature": 0.2,
            "model": "mistral:instruct",
            "enable_memory": True,
            "db_path": "./db/Web_Researcher_memory", # Add db_path to example
            "moa_role": "proposer"
        },
    ]

    ollama_request = {
        "model": st.session_state.model,
        "prompt": f"""{system_prompt}\n\nAvailable Skills: {available_skills}\n\nSchema: {json.dumps(schema)}\n\nExample: {json.dumps(json_example)}\n\nYou are an expert system designed to identify and recommend the optimal team of experts required to fulfill this specific user's request: {text} Your analysis should consider the complexity, domain, and specific needs of the request to assemble a multidisciplinary team of experts. Each recommended expert should come with a defined role, a brief description of their expertise, their skill set, and the tools they would utilize to achieve the user's goal.  For skills, choose from the "Available Skills" list.  The first agent must be qualified to manage the entire project, aggregate the work done by all the other agents, and produce a robust, complete, and reliable solution. **When choosing agent names, use only letters, numbers, and underscores.** Respond with ONLY a JSON array of experts, where each expert is an object adhering to the schema:""",
        "options": {"temperature": temperature_value},
        "stream": False,
    }
    try:
        response = requests.post(url, json=ollama_request, headers=headers, timeout=240) # Added timeout
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
                model = agent_data.get("model", "mistral:instruct")
                db_path = agent_data.get("db_path", os.path.join("./db", f"{expert_name}_memory")) # Get db_path from agent_data
                enable_memory = agent_data.get("enable_memory", False)
                moa_role = agent_data.get("moa_role", "proposer")
                autogen_agent, crewai_agent = create_agent_data(
                    expert_name, description, skills, tools, ollama_url=ollama_url, temperature=temperature, model=model, db_path=db_path, enable_memory=enable_memory, moa_role=moa_role
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
    enable_chat_manager_memory = st.session_state.get("enable_chat_manager_memory", False)
    chat_manager_db_path = st.session_state.get("chat_manager_db_path", "./db/group_chat_manager")
    workflow = {
        "name": "TeamForgeAI Workflow",  # Updated workflow name
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
                    "config_list": [{"model": "mistral:instruct"}],
                    "temperature": temperature_value,
                    "cache_seed": 42,
                    "timeout": 2400,
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
                "db_path": chat_manager_db_path,
                "enable_memory": enable_chat_manager_memory
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
    When requesting an image, use the following format: ![Image Request](description of image)
    When discussing an objective, use the following format: **Objective [number]:** [objective text]
    When discussing a deliverable, use the following format: **Deliverable [number]:** [deliverable text]
    Focus your communication on demonstrating progress towards the project objectives. 
    Before marking an objective or deliverable as complete, ensure that the corresponding tasks have been fully executed and the outcomes meet the project requirements.
    Once the user's request is fully addressed with all aspects considered, conclude your interaction with the command: TERMINATE.
    Periodically use the 'summarize_project_status' skill to provide a concise overview of the current project status, including the progress of objectives and deliverables.
    """

        agent_config = {
            "type": "assistant",
            "config": {
                "name": agent_name, # Use the original agent name
                "llm_config": {
                    "config_list": [{"model": agent["model"]}],  # Use the agent's specified model
                    "temperature": agent["temperature"],  # Use the agent's specified temperature
                    "cache_seed": 42,
                    "timeout": 2400,
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
                "db_path": agent.get("db_path", None), # Include db_path in agent config
                "enable_memory": agent.get("enable_memory", False)
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
        autogen_file_data[f"agents/{agent_file_name}"] = agent_file_data # Corrected path

    # Add skill files to the Autogen ZIP if any agent has the skill
    skills_to_add = ["fetch_web_content", "web_search", "generate_sd_images", "generate_agent_instructions", "update_project_status", "summarize_project_status", "plot_diagram"]
    for skill in skills_to_add:
        for agent_data in agents_data.values():
            if skill in agent_data.get("skills", []):
                skills_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "skills")) # Get skills directory relative to this file
                with open(os.path.join(skills_dir, f"{skill}.py"), "r", encoding="utf-8") as file:
                    autogen_file_data[f"skills/{skill}.py"] = file.read()
                break  # Only add the skill file once
        
    # Write workflow file to the Autogen ZIP
    workflow_file_name = f"{sanitize_text(workflow_data['name'])}.json"
    workflow_file_data = json.dumps(workflow_data, indent=2)
    autogen_file_data[f"workflows/{workflow_file_name}"] =   workflow_file_data

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
