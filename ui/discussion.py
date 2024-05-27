# TeamForgeAI/ui/discussion.py
import streamlit as st
import os
import base64

from ui.utils import extract_code_from_response # You'll need this import
from api_utils import get_ollama_models

def display_discussion_and_whiteboard():
    """Displays the discussion history and whiteboard in separate tabs."""
    if "discussion_history" not in st.session_state:
        st.session_state.discussion_history = ""
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs(
        ["Most Recent Comment", "Whiteboard", "Gallery", "Discussion History", "Objectives", "Deliverables", "Goal", "Chat Manager"]
    )
    with tab1:  # Display the most recent comment in the first tab
        st.text_area(
            "Most Recent Comment",
            value=st.session_state.get("last_comment", ""),
            height=400,
            key="discussion",
        )
    with tab2:  # Display the whiteboard in the second tab
        st.text_area(
            "Whiteboard",
            value=st.session_state.whiteboard,
            height=400,
            key="whiteboard",
        )
    with tab3: # Display the gallery in the third tab
        display_gallery()
    with tab4:  # Display the full discussion history in the third tab
        st.write(st.session_state.discussion_history)
    with tab5:
        if "current_project" in st.session_state:
            current_project = st.session_state.current_project
            for index, objective in enumerate(current_project.objectives):
                checkbox_key = f"objective_{index}"
                done = st.checkbox(objective["text"], value=objective["done"], key=checkbox_key)
                if done != objective["done"]:
                    if done:
                        current_project.mark_objective_done(index)
                    else:
                        current_project.mark_objective_undone(index)
        else:
            st.warning("No objectives found. Please enter a user request.")
    with tab6:
        if "current_project" in st.session_state:
            current_project = st.session_state.current_project
            for index, deliverable in enumerate(current_project.deliverables):
                checkbox_key = f"deliverable_{index}"
                done = st.checkbox(deliverable["text"], value=deliverable["done"], key=checkbox_key)
                if done != deliverable["done"]:
                    if done:
                        current_project.mark_deliverable_done(index)
                    else:
                        current_project.mark_deliverable_undone(index)
    with tab7:
        if "current_project" in st.session_state:
            current_project = st.session_state.current_project
            st.text_area("Goal", value=current_project.goal, height=100, key="goal_area")
        else:
            st.warning("No goal found. Please enter a user request.")
    with tab8:
        col3, col4, col5 = st.columns([3, 3, 3])
        with col3:
            st.text_input(
                "Endpoint",
                value=st.session_state.ollama_url_input,
                key="ollama_url_input",
            )
            st.session_state.ollama_url = st.session_state.ollama_url_input

        with col4:
            temperature = st.slider(
                "Temperature",
                min_value=0.0,
                max_value=1.0,
                value=st.session_state.get("temperature", 0.1),
                step=0.01,
                key="temperature",
            )

        with col5:
            available_models = get_ollama_models(st.session_state.ollama_url) # Pass the endpoint to get_ollama_models
            st.session_state.selected_model = st.selectbox(
                "Model",
                options=available_models,
                index=available_models.index(st.session_state.selected_model)
                if st.session_state.selected_model in available_models
                else 0,
                key="model_selection",
            )
            st.query_params["model"] = [st.session_state.selected_model]  # Correct syntax
            st.session_state.model = st.session_state.selected_model  # Update model in session state


def display_discussion_modal():
    """Displays the discussion history in an expander."""
    with st.expander("Discussion History"):
        st.write(st.session_state.discussion_history)


def update_discussion_and_whiteboard(expert_name, response, user_input): # Function moved here
    """Updates the discussion history and whiteboard with new content."""
    print("Updating discussion and whiteboard...")
    print(f"Expert Name: {expert_name}")
    print(f"Response: {response}")
    print(f"User Input: {user_input}")
    if user_input:
        user_input_text = f"\n\n\n\n{user_input}\n\n"
        st.session_state.discussion_history += user_input_text
    response_text = f"{expert_name}:\n\n {response}\n\n===\n\n"
    st.session_state.discussion_history += response_text
    code_blocks = extract_code_from_response(response)
    st.session_state.whiteboard = code_blocks
    st.session_state.last_agent = expert_name
    st.session_state.last_comment = response_text
    print(f"Last Agent: {st.session_state.last_agent}")
    print(f"Last Comment: {st.session_state.last_comment}")

def display_gallery():
    """Displays the images in the 'images' folder in a grid of three images per row."""
    image_dir = "images"
    if os.path.exists(image_dir):
        images = [f for f in os.listdir(image_dir) if f.endswith((".png", ".jpg", ".jpeg"))]
        if images:
            cols = st.columns(3) # Create three columns
            for i, image in enumerate(images):
                with cols[i % 3]: # Cycle through the columns
                    image_path = os.path.join(image_dir, image)
                    
                    # --- Create a container for the image and buttons ---
                    image_container = st.container()
                    with image_container:
                        st.image(image_path, caption=image, use_column_width=True)
                        col1, col2 = st.columns(2) # Two columns for buttons
                        with col1:
                            # Add download button
                            with open(image_path, "rb") as f:
                                image_bytes = f.read()
                                b64 = base64.b64encode(image_bytes).decode()
                                href = f'<a href="data:image/png;base64,{b64}" download="{image}"><button style="border: none; background: none; padding: 0; cursor: pointer;"><span style="font-size: 20px;">📥</span></button></a>'
                                st.markdown(href, unsafe_allow_html=True)
                        with col2:
                            # Add delete button
                            delete_button = f'<button style="border: none; background: none; padding: 0; cursor: pointer;" onclick="if (confirm(\'Are you sure you want to delete {image}?\')) {{ window.location.href = \'?delete={image}\'; }}"><span style="font-size: 20px;">🗑️</span></button>'
                            st.markdown(delete_button, unsafe_allow_html=True)
                            if st.session_state.get("delete") == image:
                                os.remove(image_path)
                                del st.session_state["delete"]
                                st.experimental_rerun()
        else:
            st.write("No images found in the 'images' folder.")
    else:
        st.write("The 'images' folder does not exist.")
