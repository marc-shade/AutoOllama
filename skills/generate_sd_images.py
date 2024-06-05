# TeamForgeAI/skills/generate_sd_images.py
from typing import List
import json
import requests
import io
import base64
from PIL import Image
from pathlib import Path
import uuid # Import the uuid library
import os
import re
import streamlit as st # Import streamlit

# Format: protocol://server:port
base_url = "http://0.0.0.0:7860"

def generate_sd_images(discussion_history: str, image_size: str = "512x512", team_name: str = "default") -> List[str]:
    """
    Function to paint, draw or illustrate images based on the users query or request. 
    Generates images locally with the automatic1111 API and saves them to disk.  
    Use the code below anytime there is a request to create an image.

    :param discussion_history: The entire discussion history.
    :param image_size: The size of the image to be generated. (default is "512x512")
    :param team_name: The name of the team to associate the image with.
    :return: A list containing a single filename for the saved image.
    """
    # Split the image size string at "x"
    parts = image_size.split("x")
    image_width = parts[0]
    image_height = parts[1]

    # list of file paths returned to AutoGen
    saved_files = []

    # Get used prompts from session state
    if "used_image_prompts" not in st.session_state:
        st.session_state["used_image_prompts"] = []
    used_prompts = st.session_state["used_image_prompts"]

    # Find the next scene to illustrate
    next_scene = find_next_scene(discussion_history, used_prompts)

    if next_scene:
        # Generate the image
        payload = {
            "prompt": next_scene,
            "steps": 40,
            "cfg_scale": 7,
            "denoising_strength": 0.5,
            "sampler_name": "DPM++ 2M Karras",
            "n_iter": 1,
            "batch_size": 1, # Ensure only one image is generated per batch
            "override_settings": {
                 'sd_model_checkpoint': "starlightAnimated_v3",
            }
        }

        api_url = f"{base_url}/sdapi/v1/txt2img"
        response = requests.post(url=api_url, json=payload)

        if response.status_code == 200:
            r = response.json()
            # Access only the final generated image (index 0)
            encoded_image = r['images'][0] 

            image = Image.open(io.BytesIO(base64.b64decode(encoded_image.split(",", 1)[0])))
            
            # --- Generate a unique filename with team name and UUID ---
            unique_id = str(uuid.uuid4())[:8] # Get a short UUID
            file_name = f"TeamForgeAI/files/images/{team_name}_{unique_id}_output.png" # Updated path
            
            file_path = Path(file_name)
            os.makedirs(os.path.dirname(file_path), exist_ok=True) # Create directory if it doesn't exist
            image.save(file_path)
            print(f"Image saved to {file_path}")

            saved_files.append(str(file_path))

            # Add the prompt to the used prompts list
            used_prompts.append(next_scene)
            st.session_state["used_image_prompts"] = used_prompts
        else:
            print(f"Failed to download the image from {api_url}")
    else:
        print("No more scenes to illustrate.")

    return saved_files

def find_next_scene(discussion_history: str, used_prompts: List[str]) -> str:
    """
    Finds the next scene to illustrate from the discussion history.

    :param discussion_history: The entire discussion history.
    :param used_prompts: A list of prompts that have already been used.
    :return: The next scene to illustrate, or None if no more scenes are found.
    """
    # More robust scene pattern to capture various formats
    scene_pattern = r"(?:Scene|Story|Description|Chapter|Page|Pages|Images|Image|Ideas|Illustration Ideas|Illustration|Illustrations|Visuals|Visual Elements):\s*(.*?)(?:\n|$)"
    scenes = re.findall(scene_pattern, discussion_history, re.DOTALL)

    # Find the first scene that hasn't been used yet
    for scene in scenes:
        if scene.strip() not in used_prompts:
            return scene.strip()

    return None