# TeamForgeAI/agent_interactions.py
import re
import time
import json # Import the json module

import streamlit as st

from api_utils import send_request_to_ollama_api
from file_utils import load_skills
from skills.fetch_web_content import fetch_web_content
from skills.generate_sd_images import generate_sd_images
from skills.project_management import update_checklists # Import the new function
from ui.discussion import update_discussion_and_whiteboard  # Corrected import
from ui.utils import extract_keywords  # Import extract_keywords


def process_agent_interaction(agent_index):
    """Handles the interaction with a selected agent."""
    print("Processing agent interaction...")
    print(
        "Session state:", st.session_state
    )  # Log the session state when this function is called

    # --- Use st.session_state.agents_data to access the agents ---
    if "agents_data" not in st.session_state:
        st.session_state.agents_data = []

    agent = st.session_state.agents_data[agent_index]
    available_skills = load_skills()  # Load available skills
    selected_skill = agent.get("skill", None)  # Get the agent's selected skill

    # --- Check if the image generation skill should be triggered ---
    if st.session_state.get("generate_image_trigger", False):
        query = st.session_state.get("discussion_history", "")
        generate_and_display_image(query)
        st.session_state["generate_image_trigger"] = False  # Reset the trigger
        return  # Exit early after image generation

    # --- Otherwise, proceed with regular agent interaction or other skills ---
    agent_name = agent["config"]["name"]
    description = agent["description"]
    user_request = st.session_state.get("user_request", "")
    user_input = st.session_state.get("user_input", "")
    rephrased_request = st.session_state.get("rephrased_request", "")

    reference_url = st.session_state.get("reference_url", "")
    url_content = fetch_web_content(reference_url) if reference_url else ""

    # --- Construct the request based on the selected skill ---
    request = f"""Act as the {agent_name} who {description}.
        Original request was: {user_request}. 
        You are helping a team work on satisfying {rephrased_request}. 
        Additional input: {user_input}. 
        Reference URL content: {url_content}.
        The discussion so far has been {st.session_state.discussion_history[-50000:]}."""

    # --- Prepare the query based on the skill ---
    if selected_skill:  # If a skill is selected for the agent
        if selected_skill == "web_search":
            keywords = extract_keywords(rephrased_request) + extract_keywords(
                st.session_state.get("discussion_history", "")
            )
            query = " ".join(keywords)
            request += f"\nYou have been tasked to use the '{selected_skill}' skill to research the following query: '{query}'."
        elif selected_skill == "plot_diagram": # Update query for plot_diagram
            query = '{}' # Pass an empty JSON string as a placeholder
            request += f"\nYou have been tasked to use the '{selected_skill}' skill. Analyze the discussion history and determine if there is any data that can be visualized as a diagram. If so, extract the relevant data, interpret keywords, numerical values, and patterns to generate a JSON string with the appropriate parameters for the 'plot_diagram' skill, and then use the skill to create the diagram. If no relevant data is found, or if the user has provided specific instructions for the diagram, follow those instructions instead. Remember to always provide a valid JSON string as parameters for the 'plot_diagram' skill, even if it's an empty dictionary '{{}}'."
        else:  # Handle other skills
            query = user_input
            request += f"\nYou have been tasked to use the '{selected_skill}' skill with the following input: '{query}'."

    # --- If a skill other than generate_sd_images is selected, execute it ---
    if selected_skill and selected_skill != "generate_sd_images":
        skill_function = available_skills[selected_skill]
        skill_result = skill_function(query=query) # Pass the query to the skill function

        # --- Handle plot_diagram skill result ---
        if selected_skill == "plot_diagram":
            if skill_result.startswith("Error:"):
                st.error(skill_result)
            else:
                st.image(skill_result, caption="Generated Diagram")
        else:
            if isinstance(skill_result, list):
                formatted_results = "\n".join(
                    [f"- {title}: {url} ({snippet})" for title, url, snippet in skill_result]
                )
                response_text = formatted_results
            else:
                response_text = f"Skill '{selected_skill}' result: {skill_result}"

            update_discussion_and_whiteboard(agent_name, response_text, user_input)

        st.session_state["trigger_rerun"] = True
        return  # Exit after executing the skill

    
    # Reset the UI update flag
    st.session_state["update_ui"] = False

    # --- If no skill is selected, get the agent's response from the LLM ---
    response_generator = send_request_to_ollama_api(agent_name, request)
    full_response = ""
    for response_chunk in response_generator:
        response_text = response_chunk.get("response", "")
        full_response += response_text
        st.session_state["accumulated_response"] = full_response
        st.session_state["trigger_rerun"] = True

    update_discussion_and_whiteboard(agent_name, full_response, user_input)
    st.session_state["form_agent_name"] = agent_name
    st.session_state["form_agent_description"] = description
    st.session_state["selected_agent_index"] = agent_index
    st.session_state["trigger_rerun"] = True

    # --- Update checklists after agent interaction ---
    if "Project Manager" in agent_name or agent_name == "Chat Manager":
        update_checklists(st.session_state.discussion_history, st.session_state.current_project)
        st.session_state["trigger_rerun"] = True # Trigger a rerun to reflect the changes


def generate_and_display_image(query):
    """Generates an image using the generate_sd_images skill and displays it."""
    
    # --- Generate a unique seed for each image ---
    if "image_seed_counter" not in st.session_state:
        st.session_state["image_seed_counter"] = 1  # Start counter from 1
    current_seed = st.session_state["image_seed_counter"]
    st.session_state["image_seed_counter"] += 1

    image_paths = generate_sd_images(
        query=query, seed=current_seed
    )

    try:
        # Assuming generate_sd_images returns a list of image file paths
        time.sleep(1)
        # Display the generated images
        if image_paths is not None:
            for image_path in image_paths:
                with open(image_path, "rb") as f:
                    image_bytes = f.read()
                    st.image(image_bytes, caption=f"Generated Image: {image_path}")
        else:
            print(f"generate_sd_images did not return any images")

    except Exception as e:
        print(f"Error executing generated code: {e}")
        st.error(f"Error generating image: {e}")
