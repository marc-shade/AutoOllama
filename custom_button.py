# TeamForgeAI/custom_button.py
import streamlit.components.v1 as components

def custom_button(expert_name: str, index: int, next_agent: str) -> None:
    """
    Generate a custom button with specific styles and behaviors.

    Args:
        expert_name (str): The text to display on the button.
        index (int): Unused in this implementation, but could be used for indexing or sorting purposes.
        next_agent (str): The next agent to highlight as active.

    Returns: None
    """
    # Create a CSS style block with two classes: .custom-button and .custom-button.active
    button_style = """
    <style>
    .custom-button {
        background-color: #f0f0f0;
        color: black;
        padding: 0rem 0.3rem;
        border: none;
        border-radius: 0.25rem;
        cursor: pointer;
    }
    .custom-button.active {
        background-color: green;
        color: white;
    }
    </style>
    """

    # Determine the class name for the button based on whether it's the active agent or not
    button_class = "custom-button active" if next_agent == expert_name else "custom-button"

    # Generate an HTML button element with the specified text and class name
    button_html = f'<button class="{button_class}">{expert_name}</button>'

    # Render the HTML code for the button using Streamlit's components.html function
    components.html(button_style + button_html, height=50)

def agent_button(expert_name: str, index: int, next_agent: str) -> None:
    """
    Call the custom_button function to generate a custom button.

    Args:
        expert_name (str): The text to display on the button.
        index (int): Unused in this implementation, but could be used for indexing or sorting purposes.
        next_agent (str): The next agent to highlight as active.

    Returns: None
    """
    custom_button(expert_name, index, next_agent)