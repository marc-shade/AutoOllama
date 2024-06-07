import streamlit as st
import os
import base64
import json
import pandas as pd

from ui.utils import extract_code_from_response, display_download_button, list_discussions, load_discussion_history
from api_utils import get_ollama_models
from skills.plot_diagram import plot_diagram

# Define custom CSS
CUSTOM_CSS = """
<style>
.main div.stButton button {
    padding: 0px !important;
    background-color: transparent !important;
    color: #000000 !important;
    border: none !important;
    cursor: pointer !important;
}
</style>
"""

# Inject custom CSS
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

def handle_checkbox_change(key: str, value: bool) -> None:
    """Callback function to handle checkbox changes."""
    if "current_project" in st.session_state:
        current_project = st.session_state.current_project
        if key.startswith("objective_"):
            index = int(key.split("_")[1])
            if value:
                current_project.mark_objective_done(index)
            else:
                current_project.mark_objective_undone(index)
        elif key.startswith("deliverable_"):
            index = int(key.split("_")[1])
            if value:
                current_project.mark_deliverable_done(index)
            else:
                current_project.mark_deliverable_undone(index)
        st.session_state.current_project = current_project

def display_discussion_and_whiteboard() -> None:
    """Displays the discussion history and whiteboard in separate tabs."""
    if "discussion_history" not in st.session_state:
        st.session_state.discussion_history = ""
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs(
        ["Most Recent Comment", "Whiteboard", "Gallery", "Charts", "Discussion History", "Objectives", "Deliverables", "Goal", "Chat Manager"]
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
    with tab3:  # Display the gallery in the third tab
        display_gallery()
    with tab4:  # Charts tab
        st.header("Charts")
        if 'chart_data' in st.session_state:
            try:
                chart_data = json.loads(st.session_state.chart_data)
                df = pd.DataFrame(chart_data)
                st.area_chart(df.set_index('x'))
            except Exception as e:
                st.error(f"Error: Invalid data format for chart: {e}")
        else:
            st.warning("No chart data available.")
    with tab5:  # Display the full discussion history in the fifth tab
        st.write(st.session_state.discussion_history)

        # Moved 'Load Previous Discussion' and download buttons inside 'Discussion History' tab
        discussions = list_discussions()
        selected_discussion = st.selectbox("Load Previous Discussion", [""] + discussions, index=0, key="discussion_selectbox")
        if selected_discussion:
            st.session_state.selected_discussion = selected_discussion
            st.session_state.discussion_history = load_discussion_history(selected_discussion)

    with tab6:  # Objectives tab
        if "current_project" in st.session_state:
            current_project = st.session_state.current_project
            for index, objective in enumerate(current_project.objectives):
                checkbox_key = f"objective_{index}"
                # Link the checkbox to the handle_checkbox_change function
                st.checkbox(objective["text"], value=objective["done"], key=checkbox_key, on_change=handle_checkbox_change, args=(checkbox_key, not objective["done"]))
            st.session_state.current_project = current_project  # Update the session state
        else:
            st.warning("No objectives found. Please enter a user request.")
    with tab7:  # Deliverables tab
        if "current_project" in st.session_state:
            current_project = st.session_state.current_project
            for index, deliverable in enumerate(current_project.deliverables):
                checkbox_key = f"deliverable_{index}"
                # Link the checkbox to the handle_checkbox_change function
                st.checkbox(deliverable["text"], value=deliverable["done"], key=checkbox_key, on_change=handle_checkbox_change, args=(checkbox_key, not deliverable["done"]))
            st.session_state.current_project = current_project  # Update the session state
    with tab8:  # Goal tab
        if "current_project" in st.session_state:
            current_project = st.session_state.current_project
            st.text_area("Goal", value=current_project.goal, height=100, key="goal_area")
        else:
            st.warning("No goal found. Please enter a user request.")
    with tab9:  # Chat Manager tab
        column3, column4, column5 = st.columns([3, 3, 3])
        with column3:
            st.text_input(
                "Endpoint",
                value=st.session_state.ollama_url_input,
                key="ollama_url_input",
            )
            st.session_state.ollama_url = st.session_state.ollama_url_input

        with column4:
            temperature = st.slider(
                "Temperature",
                min_value=0.0,
                max_value=1.0,
                value=st.session_state.get("temperature", 0.1),
                step=0.01,
                key="temperature",
            )

        with column5:
            available_models = get_ollama_models(st.session_state.ollama_url)  # Pass the endpoint to get_ollama_models
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


def display_discussion_modal() -> None:
    """Displays the discussion history in an expander."""
    with st.expander("Discussion History"):
        st.write(st.session_state.discussion_history)


def update_discussion_and_whiteboard(expert_name: str, response: str, user_input: str) -> None:
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

def display_gallery() -> None:
    """Displays the images in the 'images' folder in a grid of three images per row."""
    image_dir = "TeamForgeAI/files/images"  # Updated path
    if os.path.exists(image_dir):
        images = [file for file in os.listdir(image_dir) if file.endswith((".png", ".jpg", ".jpeg"))]
        if images:
            if 'images_to_delete' not in st.session_state:
                st.session_state.images_to_delete = []

            columns = st.columns(3)  # Create three columns
            for i, image in enumerate(images):
                if image in st.session_state.images_to_delete:
                    continue

                with columns[i % 3]:  # Cycle through the columns
                    image_path = os.path.join(image_dir, image)
                    
                    # --- Create a container for the image and buttons ---
                    image_container = st.container()
                    with image_container:
                        st.image(image_path, caption=image, use_column_width=True)
                        column1, column2 = st.columns(2)  # Two columns for buttons
                        with column1:
                            # Add download button
                            with open(image_path, "rb") as file:
                                image_bytes = file.read()
                                base64_image = base64.b64encode(image_bytes).decode()
                                href = f'<a href="data:image/png;base64,{base64_image}" download="{image}"><button style="border: none; background: none; padding: 0; cursor: pointer;"><span style="font-size: 20px;">📥</span></button></a>'
                                st.markdown(href, unsafe_allow_html=True)
                        with column2:
                            # Add delete button
                            if st.button("🗑️", key=f"delete_{image}"):
                                st.session_state.images_to_delete.append(image)
                                os.remove(image_path)
                                st.rerun()
        else:
            st.write("No images found in the 'images' folder.")
    else:
        st.write("The 'images' folder does not exist.")
