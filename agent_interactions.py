# TeamForgeAI/agent_interactions.py
import time
import json # Import the json module
import re # Import the re module

import streamlit as st

from api_utils import send_request_to_ollama_api
from file_utils import load_skills
from skills.fetch_web_content import fetch_web_content
from skills.generate_sd_images import generate_sd_images
from skills.update_project_status import update_checklists # Updated import
from skills.summarize_project_status import summarize_project_status
from ui.discussion import update_discussion_and_whiteboard  # Corrected import
from ui.utils import extract_keywords  # Import extract_keywords
from ollama_llm import OllamaLLM # Import OllamaLLM from ollama_llm.py
from skills.web_search import web_search # Import web_search directly
from agent_creation import create_autogen_agent # Import create_autogen_agent

def process_agent_interaction(agent_index: int) -> None:
    """Handles the interaction with a selected agent."""
    print("Processing agent interaction...")
    print(
        "Session state:", st.session_state
    )  # Log the session state when this function is called

    # --- Use st.session_state.agents_data to access the agents ---
    if "agents_data" not in st.session_state:
        st.session_state.agents_data = []

    agent_data = st.session_state.agents_data[agent_index] # Get the agent data
    # Create an instance of OllamaConversableAgent from the agent_instance dictionary
    agent_instance = create_autogen_agent(agent_data)
    available_skills = load_skills()  # Load available skills
    selected_skill = agent_data.get("skill", [])  # Get the agent's selected skill from agent_data, default to an empty list

    # --- Check if the image generation skill should be triggered ---
    if st.session_state.get("generate_image_trigger", False):
        discussion_history = st.session_state.get("discussion_history", "")
        generate_and_display_images(discussion_history) # Call the new function to handle multiple images
        st.session_state["generate_image_trigger"] = False  # Reset the trigger
        return  # Exit early after image generation

    # --- Otherwise, proceed with regular agent interaction or other skills ---
    agent_name = agent_data["config"]["name"] # Access from agent_data
    description = agent_data["description"] # Access from agent_data
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
        if selected_skill[0] == "web_search":
            keywords = extract_keywords(rephrased_request) + extract_keywords(
                st.session_state.get("user_request", "") # Use the original user request instead of the formatted discussion history
             )
            query = " ".join(keywords)
            # Call the web_search function directly
            skill_result = web_search(query, st.session_state.discussion_history, st.session_state.agents_data, agent_instance.teachability) # Use agent_instance.teachability
            response_text = f"Skill '{selected_skill[0]}' result: {skill_result}"
            update_discussion_and_whiteboard(agent_name, response_text, user_input)
            return
        elif selected_skill[0] == "plot_diagram": # Update query for plot_diagram
            query = '{}' # Pass an empty JSON string as a placeholder
            request += f"\nYou have been tasked to use the '{selected_skill[0]}' skill. Analyze the discussion history and determine if there is any data that can be visualized as a diagram. If so, extract the relevant data, interpret keywords, numerical values, and patterns to generate a JSON string with the appropriate parameters for the 'plot_diagram' skill, and then use the skill to create the diagram. If no relevant data is found, or if the user has provided specific instructions for the diagram, follow those instructions instead. Remember to always provide a valid JSON string as parameters for the 'plot_diagram' skill, even if it's an empty dictionary '{{}}'."
        elif selected_skill[0] in ["generate_agent_instructions", "update_project_status", "summarize_project_status"]: # Handle new skills
            query = "" # These skills don't require a query
        else:  # Handle other skills
            query = user_input
            request += f"\nYou have been tasked to use the '{selected_skill[0]}' skill with the following input: '{query}'."

    # --- If a skill other than generate_sd_images is selected, execute it ---
    if selected_skill and selected_skill[0] != "generate_sd_images":
        skill_function = available_skills[selected_skill[0]]
        if selected_skill[0] in ["web_search", "fetch_web_content"]:
            skill_result = skill_function(query=query, discussion_history=st.session_state.discussion_history, teachability=agent_instance.teachability) # Pass teachability to skill_function
        elif selected_skill[0] == "plot_diagram":
            skill_result = skill_function(query=query, discussion_history=st.session_state.discussion_history) # Pass the query to the skill function
        else:
            skill_result = skill_function(query=query, agents_data=st.session_state.agents_data, discussion_history=st.session_state.discussion_history) # Pass the query to the skill function

        # --- Handle plot_diagram skill result ---
        if selected_skill[0] == "plot_diagram":
            if skill_result.startswith("Error:"):
                st.error(skill_result)
            else:
                st.session_state.chart_data = skill_result # Store chart data in session state
                st.session_state.trigger_rerun = True # Trigger a rerun to display the chart

            return  # Exit after executing the skill

        if isinstance(skill_result, list):
            formatted_results = "\n".join(
                [f"- {title}: {url} ({snippet})" for title, url, snippet in skill_result]
            )
            response_text = formatted_results
        else:
            response_text = f"Skill '{selected_skill[0]}' result: {skill_result}"

        update_discussion_and_whiteboard(agent_name, response_text, user_input)
        return

    # --- Add user input to the discussion history BEFORE sending to LLM ---
    if user_input:
        user_input_text = f"\n\n\n\n{user_input}\n\n"
        st.session_state.discussion_history += user_input_text
        st.session_state["trigger_rerun"] = True # Trigger a rerun to display the update

    # Reset the UI update flag
    st.session_state["update_ui"] = False

    # --- If no skill is selected, get the agent's response from the LLM ---
    if agent_data.get("enable_moa", False): # Access from agent_data
        full_response = execute_moa_workflow(request, st.session_state.agents_data, agent_data) # Pass agent_data
        # Update discussion history with MoA response
        update_discussion_and_whiteboard(agent_name, full_response, user_input)
    else:
        # Check if memory is enabled
        if agent_data.get("enable_memory", False):
            # Store the user input in the agent's memory using add_message
            agent_instance.add_message("User", user_input)  # Call add_message on the agent instance

        response_generator = send_request_to_ollama_api(agent_name, request, agent_data=agent_data) # Pass agent_data
        full_response = ""
        for response_chunk in response_generator:
            if 'done' in response_chunk and response_chunk['done']: # Check if the response is complete
                response_text = response_chunk.get("response", "")
                full_response += response_text

                # --- Enforce image request format before updating discussion history ---
                full_response = enforce_image_request_format(full_response)

                # --- Update the discussion history AFTER the response is complete ---
                update_discussion_and_whiteboard(agent_name, full_response, user_input)
                st.session_state["accumulated_response"] = full_response
                st.session_state["trigger_rerun"] = True # Set the flag to trigger a rerun
                break # Exit the loop since the response is complete
            response_text = response_chunk.get("response", "")
            full_response += response_text
            st.session_state["accumulated_response"] = full_response
            st.session_state["trigger_rerun"] = True # Set the flag to trigger a rerun

    # --- Removed duplicate call to update_discussion_and_whiteboard ---

    st.session_state["form_agent_name"] = agent_name
    st.session_state["form_agent_description"] = description
    st.session_state["selected_agent_index"] = agent_index
    # --- Removed st.rerun() from here ---

    # --- Update checklists after agent interaction ---   
    if "current_project" in st.session_state:
        update_checklists(st.session_state.discussion_history, st.session_state.current_project)
        st.session_state.current_project = st.session_state.current_project # Update session state
        # --- Set the flag to trigger a rerun ---
        st.session_state["trigger_rerun"] = True


def generate_and_display_images(discussion_history: str) -> None:
    """Generates images using the generate_sd_images skill and displays them."""

    while True: # Keep generating images until there are no more scenes
        image_paths = generate_sd_images(
            discussion_history=discussion_history # Pass discussion_history to generate_sd_images
        )

        try:
            # Assuming generate_sd_images returns a list of image file paths
            time.sleep(1)
            # Display the generated images
            if image_paths is not None:
                for image_path in image_paths:
                    with open(image_path, "rb") as file:
                        image_bytes = file.read()
                        st.image(image_bytes, caption=f"Generated Image: {image_path}")
            else:
                print(f"generate_sd_images did not return any images")
                break # Exit the loop if no images were generated

        except Exception as error:
            print(f"Error executing generated code: {error}")
            st.error(f"Error generating image: {error}")
            break # Exit the loop if there was an error

def enforce_image_request_format(text: str) -> str:
    """
    Enforces the standardized image request format in the agent's response.

    :param text: The agent's response text.
    :return: The text with image requests formatted correctly.
    """
    image_request_pattern = r"(?:Image|Illustration|Visual):\s*(.*?)(?:\n|$)"
    image_requests = re.findall(image_request_pattern, text)
    for image_request in image_requests:
        text = text.replace(f"Image: {image_request}", f"![Image Request]({image_request})")
        text = text.replace(f"Illustration: {image_request}", f"![Image Request]({image_request})")
        text = text.replace(f"Visual: {image_request}", f"![Image Request]({image_request})")
    return text

def execute_moa_workflow(request: str, agents_data: list, current_agent: dict) -> str:
    """Executes the Mixture-of-Agents workflow."""
    # Separate proposers and aggregators
    proposers = [agent for agent in agents_data if agent.get("moa_role") == "proposer"]
    aggregators = [agent for agent in agents_data if agent.get("moa_role") == "aggregator"]

    # Layer 1: Proposers generate initial responses
    layer_1_outputs = []
    for proposer in proposers:
        ollama_llm = OllamaLLM(
            base_url=proposer["ollama_url"],
            model=proposer["model"],
            temperature=proposer["temperature"]
        )
        response = ollama_llm.generate_text(request)
        layer_1_outputs.append(response)

    # Subsequent layers: Aggregators refine responses
    current_responses = layer_1_outputs
    for i in range(2, 4):  # Adjust the number of layers as needed
        new_responses = []
        for aggregator in aggregators:
            ollama_llm = OllamaLLM(
                base_url=aggregator["ollama_url"],
                model=aggregator["model"],
                temperature=aggregator["temperature"]
            )
            aggregate_prompt = f"""You have been provided with a set of responses from various open-source models to the latest user query. Your task is to synthesize these responses into a single, high-quality response. It is crucial to critically evaluate the information provided in these responses, recognizing that some of it may be biased or incorrect. Your response should not simply replicate the given answers but should offer a refined, accurate, and comprehensive reply to the instruction. Ensure your response is well-structured, coherent, and adheres to the highest standards of accuracy and reliability.

            Responses from models:
            {chr(10).join([f'{j+1}. {response}' for j, response in enumerate(current_responses)])}
            """
            response = ollama_llm.generate_text(aggregate_prompt)
            new_responses.append(response)
        current_responses = new_responses

    # Final output: Use the current agent as the final aggregator
    ollama_llm = OllamaLLM(
        base_url=current_agent["ollama_url"],
        model=current_agent["model"],
        temperature=current_agent["temperature"]
    )
    aggregate_prompt = f"""You have been provided with a set of responses from various open-source models to the latest user query. Your task is to synthesize these responses into a single, high-quality response. It is crucial to critically evaluate the information provided in these responses, recognizing that some of it may be biased or incorrect. Your response should not simply replicate the given answers but should offer a refined, accurate, and comprehensive reply to the instruction. Ensure your response is well-structured, coherent, and adheres to the highest standards of accuracy and reliability.

    Responses from models:
    {chr(10).join([f'{j+1}. {response}' for j, response in enumerate(current_responses)])}
    """
    moa_response = ollama_llm.generate_text(aggregate_prompt)
    return moa_response
