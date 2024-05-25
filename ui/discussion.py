# TeamForgeAI/ui/discussion.py
import streamlit as st

from ui.utils import extract_code_from_response # You'll need this import

def display_discussion_and_whiteboard():
    """Displays the discussion history and whiteboard in separate tabs."""
    if "discussion_history" not in st.session_state:
        st.session_state.discussion_history = ""
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
        ["Most Recent Comment", "Whiteboard", "Discussion History", "Objectives", "Deliverables", "Goal"]
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
    with tab3:  # Display the full discussion history in the third tab
        st.write(st.session_state.discussion_history)
    with tab4:
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
    with tab5:
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
    with tab6:
        if "current_project" in st.session_state:
            current_project = st.session_state.current_project
            st.text_area("Goal", value=current_project.goal, height=100, key="goal_area")
        else:
            st.warning("No goal found. Please enter a user request.")


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
