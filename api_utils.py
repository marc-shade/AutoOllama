# TeamForgeAI/api_utils.py
import json
import re
import time

import requests
import streamlit as st

def make_api_request(url: str, data: dict, headers: dict, api_key: str = None, timeout: int = 60) -> dict:
    """Makes an API request and returns the JSON response."""
    time.sleep(2)  # Throttle the request to ensure at least 2 seconds between calls
    try:
        response = requests.post(url, json=data, headers=headers, timeout=timeout)
        if response.status_code == 200:
            return response.json()
        print(
            f"Error: API request failed with status {response.status_code}, response: {response.text}"
        )
        return None
    except requests.RequestException as error:
        print(f"Error: Request failed {error}")
        return None


def create_agent_data(
    expert_name: str, description: str, skills: list, tools: list, enable_reading_html: bool = False, ollama_url: str = None, temperature: float = None, model: str = None
) -> tuple:  # Add enable_reading_html argument
    """Creates agent data for both AutoGen and CrewAI agents."""
    autogen_agent_data = {
        "type": "assistant",
        "config": {
            "name": expert_name,
            "llm_config": {
                "config_list": [{"model": "llama3:8b"}],  # Default to Llama3
                "temperature": temperature if temperature is not None else 0.1,
                "timeout": 600,
                "cache_seed": 42,
            },
            "human_input_mode": "NEVER",
            "max_consecutive_auto_reply": 8,
            "system_message": f"You are a helpful assistant that can act as {expert_name} who {description}.",
        },
        "description": description,
        "skills": skills,
        "tools": tools,
        "enable_reading_html": enable_reading_html,
        "ollama_url": ollama_url, # Add agent-specific settings
        "temperature": temperature,
        "model": model,
    }
    crewai_agent_data = {
        "name": expert_name,
        "description": description,
        "skills": skills,
        "tools": tools,
        "verbose": True,
        "allow_delegation": True,
    }
    return autogen_agent_data, crewai_agent_data


def send_request_to_ollama_api(expert_name: str, request: str, api_key: str = None, stream: bool = True, agent: dict = None, timeout: int = 60): # Add agent parameter
    """Sends a request to the Ollama API and yields the response."""
    # --- Get agent-specific settings or fall back to global settings ---
    ollama_url = agent.get("ollama_url") if agent else st.session_state.get("ollama_url", "http://localhost:11434")
    temperature_value = agent.get("temperature") if agent else st.session_state.get("temperature", 0.1)
    # --- Use agent-specific model if available ---
    model = agent.get("model") if agent else st.session_state.get("model", "mistral:7b-instruct-v0.2-q8_0")

    url = f"{ollama_url}/api/generate"
    data = {
        "model": model, # Use agent-specific model
        "prompt": request,
        "options": {
            "temperature": temperature_value, # Use agent-specific temperature
        },
        "stream": stream,  # Include stream parameter
    }
    headers = {
        "Content-Type": "application/json",
    }

    if stream:
        try:
            response = requests.post(url, json=data, headers=headers, stream=True, timeout=timeout)
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode("utf-8")
                    json_response = json.loads(decoded_line)
                    # Update session state to trigger UI update
                    st.session_state["update_ui"] = True
                    st.session_state["next_agent"] = expert_name
                    yield json_response
        except requests.exceptions.RequestException as e:
            st.error(f"Request failed: {e}")
            return None
    else:
        try:
            response = requests.post(url, json=data, headers=headers, timeout=timeout)
            if response.status_code == 200:           
               return response.json()  # Return the JSON response directly
            print(
                f"Error: API request failed with status {response.status_code}, response: {response.text}"
            )
            return None
        except requests.exceptions.RequestException as e:
            st.error(f"Request failed: {e}")
            return None


def extract_code_from_response(response: str) -> str:
    """Extracts code blocks from the response."""
    code_pattern = r"```(.*?)```"
    code_blocks = re.findall(code_pattern, response, re.DOTALL)

    html_pattern = r"```(.*?)```"
    code_blocks = re.findall(code_pattern, response, re.DOTALL)

    html_pattern = r"<html.*?>.*?</html>"
    html_blocks = re.findall(html_pattern, response, re.DOTALL | re.IGNORECASE)

    js_pattern = r"<script.*?>.*?</script>"
    js_blocks = re.findall(js_pattern, response, re.DOTALL | re.IGNORECASE)

    css_pattern = r"<style.*?>.*?</style>"
    css_blocks = re.findall(css_pattern, response, re.DOTALL | re.IGNORECASE)

    all_code_blocks = code_blocks + html_blocks + js_blocks + css_blocks
    unique_code_blocks = list(set(all_code_blocks))
    return "\n\n".join(unique_code_blocks)

def get_ollama_models(ollama_url: str = "http://localhost:11434", timeout: int = 60) -> list: # Moved from main.py
    """Gets the list of available models from the Ollama API."""
    try:
        response = requests.get(f"{ollama_url}/api/tags", timeout=timeout)
        response.raise_for_status()
        models = [
            model["name"]
            for model in response.json()["models"]
            if "embed" not in model["name"]
        ]
        models.sort()  # Simple alphabetical sorting for now
        return models
    except requests.exceptions.RequestException as error:
        st.error(f"Error fetching models: {error}")
        return []
