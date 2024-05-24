# TeamForgeAI/api_utils.py
import json
import re
import time

import requests
import streamlit as st


def make_api_request(url, data, headers, api_key=None):
    time.sleep(2)  # Throttle the request to ensure at least 2 seconds between calls
    try:
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(
                f"Error: API request failed with status {response.status_code}, response: {response.text}"
            )
            return None
    except requests.RequestException as e:
        print(f"Error: Request failed {e}")
        return None


def create_agent_data(
    expert_name, description, skills, tools, enable_reading_html=False
):  # Add enable_reading_html argument
    temperature_value = st.session_state.get("temperature", 0.1)
    autogen_agent_data = {
        "type": "assistant",
        "config": {
            "name": expert_name,
            "llm_config": {
                "config_list": [{"model": "llama3:8b"}],  # Default to Llama3
                "temperature": temperature_value,
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


def send_request_to_ollama_api(expert_name, request, api_key=None, stream=True):
    temperature_value = st.session_state.get("temperature", 0.1)
    ollama_url = st.session_state.get("ollama_url", "http://localhost:11434")

    url = f"{ollama_url}/api/generate"
    data = {
        "model": st.session_state.model,
        "prompt": request,
        "options": {
            "temperature": temperature_value,
        },
        "stream": stream,  # Include stream parameter
    }
    headers = {
        "Content-Type": "application/json",
    }

    if stream:
        response = requests.post(url, json=data, headers=headers, stream=True)
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode("utf-8")
                json_response = json.loads(decoded_line)
                # Update session state to trigger UI update
                st.session_state["update_ui"] = True
                st.session_state["next_agent"] = expert_name
                yield json_response
    else:
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            return response.json()  # Return the JSON response directly
        else:
            print(
                f"Error: API request failed with status {response.status_code}, response: {response.text}"
            )
            return None


def extract_code_from_response(response):
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