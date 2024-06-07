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
    parts = image_size.split("x")
    image_width = int(parts[0])
    image_height = int(parts[1])

    saved_files = []

    if "used_image_prompts" not in st.session_state:
        st.session_state["used_image_prompts"] = []
    used_prompts = st.session_state["used_image_prompts"]

    next_scene = find_next_scene(discussion_history, used_prompts)

    if next_scene:
        payload = {
            "prompt": next_scene,
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
        response = requests.post(url=api_url, json=payload)

        if response.status_code == 200:
            r = response.json()
            encoded_image = r['images'][0]
            image = Image.open(io.BytesIO(base64.b64decode(encoded_image.split(",", 1)[0])))

            unique_id = str(uuid.uuid4())[:8]
            file_name = f"TeamForgeAI/files/images/{team_name}_{unique_id}_output.png"

            file_path = Path(file_name)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            image.save(file_path)
            print(f"Image saved to {file_path}")

            saved_files.append(str(file_path))

            used_prompts.append(next_scene)
            st.session_state["used_image_prompts"] = used_prompts
        else:
            print(f"Failed to download the image from {api_url}")
    else:
        print("No more scenes to illustrate.")

    return saved_files

def find_next_scene(discussion_history: str, used_prompts: List[str]) -> str:
    """
    Finds the next scene to illustrate from the discussion history, considering user input and AI agent requests.

    :param discussion_history: The entire discussion history.
    :param used_prompts: A list of prompts that have already been used.
    :return: The next scene to illustrate, or None if no more scenes are found.
    """

    # 1. Check for user input image requests
    user_image_request_pattern = r"\n\n\n\nImages?:\s*(.*?)\n\n"
    user_image_requests = re.findall(user_image_request_pattern, discussion_history, re.DOTALL)
    for user_image_request in user_image_requests:
        if user_image_request not in used_prompts:
            return user_image_request

    # 2. Check for AI agent image requests
    ai_image_request_pattern = r"!\[Image Request]\((.*?)\)"
    ai_image_requests = re.findall(ai_image_request_pattern, discussion_history)
    for ai_image_request in ai_image_requests:
        if ai_image_request not in used_prompts:
            return ai_image_request

    # 3. If no explicit requests, analyze the discussion for potential image prompts
    # (You can add more sophisticated logic here based on sentiment analysis, keywords, etc.)
    # For now, we'll use the previous logic of extracting from book content
    book_content_pattern = r"Here's a(?: revised)? draft of the manuscript:\n\n(.*?)\n\n===\n\n"
    book_content_match = re.search(book_content_pattern, discussion_history, re.DOTALL)
    book_content = book_content_match.group(1) if book_content_match else ""

    scene_pattern = r"(?:Scene|Story|Description|Chapter|Page|Pages|Images|Image|Ideas|Illustration Ideas|Illustration|Illustrations|Visuals|Visual Elements):\s*(.*?)(?:\n|$)"
    scenes = re.findall(scene_pattern, book_content, re.DOTALL)

    for scene in scenes:
        scene = scene.strip()
        if scene not in used_prompts:
            return scene

    fallback_pattern = r"(?:\n|^)(.*?)(?:\n|$)"
    all_text = re.findall(fallback_pattern, book_content, re.DOTALL)

    for text in all_text:
        text = text.strip()
        if text and text not in used_prompts:
            return text

    return None
