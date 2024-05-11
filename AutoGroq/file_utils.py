# AutoOllama/file_utils.py
import os
import json
import re

def sanitize_text(text):
    # Only remove non-printable characters
    text = ''.join(c for c in text if c.isprintable())
    return text

def create_agent_data(expert_name, description, skills=None, tools=None):
    # Format the expert_name
    formatted_expert_name = sanitize_text(expert_name)
    formatted_expert_name = formatted_expert_name.lower().replace(' ', '_')
    # Sanitize the description
    sanitized_description = sanitize_text(description)
    # Sanitize the skills and tools
    sanitized_skills = [sanitize_text(skill) for skill in skills] if skills else []
    sanitized_tools = [sanitize_text(tool) for tool in tools] if tools else []
    # Create the agent data
    agent_data = {
        "type": "assistant",
        "config": {
            "name": expert_name, # Use the original expert_name here
            "llm_config": {
                "config_list": [
                    {
                        "model": "mistral"  # Default to Mistral
                    }
                ],
                "temperature": 0.1,
                "timeout": 600,
                "cache_seed": 42
            },
            "human_input_mode": "NEVER",
            "max_consecutive_auto_reply": 8,
            "system_message": f"You are a helpful assistant that can act as {expert_name} who {sanitized_description}."
        },
        "description": description, # Use the original description here
        "skills": sanitized_skills,
        "tools": sanitized_tools
    }
    crewai_agent_data = {
        "name": expert_name,
        "description": description,
        "skills": sanitized_skills,
        "tools": sanitized_tools,
        "verbose": True,
        "allow_delegation": True
    }
    return agent_data, crewai_agent_data

def create_workflow_data(workflow):
    # Sanitize the workflow name
    sanitized_workflow_name = sanitize_text(workflow["name"])
    sanitized_workflow_name = sanitized_workflow_name.lower().replace(' ', '_')

    return workflow
