# TeamForgeAI/skills/generate_sd_images.py
from typing import List
import json
import requests
import io
import base64
from PIL import Image
from pathlib import Path
import uuid
import os
import re
import streamlit as st

# Format: protocol://server:port
base_url = "http://0.0.0.0:7860"

def generate_sd_images(discussion_history: str, image_size: str = "512x512", team_name: str = "default") -> str:
    """
    Function to paint, draw or illustrate images based on the users query or request.
    Generates images locally with the automatic1111 API and saves them to disk.
    Use the code below anytime there is a request to create an image.

    :param discussion_history: The entire discussion history.
    :param image_size: The size of the image to be generated. (default is "512x512")
    :param team_name: The name of the team to associate the image with.
    :return: A message indicating the result of the image generation process.
    """
    parts = image_size.split("x")
    image_width = int(parts[0])
    image_height = int(parts[1])

    if "used_image_prompts" not in st.session_state:
        st.session_state["used_image_prompts"] = []
    used_prompts = st.session_state["used_image_prompts"]

    all_scenes = find_all_scenes(discussion_history)

    if all_scenes:
        generated_images = []
        for scene in all_scenes:
            if scene not in used_prompts:
                payload = {
                    "prompt": scene,
                    "steps": 40,
                    "cfg_scale": 7,
                    "width": image_width,
                    "height": image_height,
                    "sampler_name": "DPM++ 2M Karras",
                    "n_iter": 1,
                    "batch_size": 1,
                    "override_settings": {
                        'sd_model_checkpoint': "starlightAnimated_v3",
                    }
                }

                api_url = f"{base_url}/sdapi/v1/txt2img"
                response = requests.post(url=api_url, json=payload, timeout=120)

                if response.status_code == 200:
                    r = response.json()
                    for i in r['images']:
                        encoded_image = i
                        image = Image.open(io.BytesIO(base64.b64decode(encoded_image.split(",", 1)[0])))

                        unique_id = str(uuid.uuid4())[:8]
                        file_name = f"TeamForgeAI/files/images/{team_name}_{unique_id}_output.png"

                        file_path = Path(file_name)
                        os.makedirs(os.path.dirname(file_path), exist_ok=True)
                        image.save(file_path)
                        print(f"Image saved to {file_path}")
                        generated_images.append(f"Image generated for: {scene}")

                    used_prompts.append(scene)
                    st.session_state["used_image_prompts"] = used_prompts
                else:
                    return f"Failed to download the image from {api_url}"
            else:
                print(f"Skipping already generated image for prompt: {scene}")
        if generated_images:
            return "\n".join(generated_images)
        else:
            return "All requested images have been generated."
    else:
        return "I'm ready to create images! Please provide a list of image descriptions using the format: ![Image Request](description of image) or Images: description"

def find_all_scenes(discussion_history: str) -> List[str]:
    """
    Finds all potential scenes to illustrate from the discussion history,
    considering user input and AI agent requests.

    :param discussion_history: The entire discussion history.
    :return: A list of all potential scenes to illustrate.
    """
    all_scenes = []

    # 1. Check for user input image requests
    user_image_request_pattern = r"Images?:\s*(.*?)\n\n" # Removed extra newlines
    user_image_requests = re.findall(user_image_request_pattern, discussion_history, re.DOTALL)
    for user_image_request in user_image_requests:
        all_scenes.extend(re.split(r'\d+\.\s', user_image_request.strip())) # Split by numbered list items

    # 2. Check for AI agent image requests
    ai_image_request_pattern = r"!\[Image Request]\((.*?)\)"
    ai_image_requests = re.findall(ai_image_request_pattern, discussion_history)
    all_scenes.extend(ai_image_requests)

    # Remove empty strings and duplicates
    all_scenes = [scene.strip() for scene in all_scenes if scene.strip()]
    all_scenes = list(set(all_scenes))

    return all_scenes
