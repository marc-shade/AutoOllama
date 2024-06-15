# TeamForgeAI/ollama_llm.py
import json
import requests
import streamlit as st

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