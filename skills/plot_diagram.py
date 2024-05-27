# TeamForgeAI/skills/plot_diagram.py
import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import uuid
import json
import re

def plot_diagram(query: str = "") -> str:
    """
    Generates a plot diagram with a black background based on the provided query or extracted data.

    The query should be a JSON string with the following format:
    ```json
    {
        "base_circles": 4,
        "base_circle_color": "blue",
        "top_circle_color": "orange",
        "line_color": "grey",
        "line_width": 2
    }
    ```

    If no query is provided, the function will attempt to extract data from the discussion history.

    :param query: A JSON string containing the diagram parameters.
    :return: The file path of the generated diagram.
    """
    if not query:
        discussion_history = st.session_state.get("discussion_history", "")
        extracted_data = extract_data_from_discussion(discussion_history)
        parameters = generate_parameters_from_data(extracted_data)
    else:
        try:
            parameters = json.loads(query)
        except json.JSONDecodeError:
            return "Error: Invalid JSON string for diagram parameters."

    base_circles = parameters.get("base_circles", 4)
    base_circle_color = parameters.get("base_circle_color", "blue")
    top_circle_color = parameters.get("top_circle_color", "orange")
    line_color = parameters.get("line_color", "grey")
    line_width = parameters.get("line_width", 2)

    # Generate a unique filename using UUID
    unique_id = str(uuid.uuid4())[:8]
    file_name = f"diagram_{unique_id}"

    # Define the directory and save path
    directory = 'diagrams'
    if not os.path.exists(directory):
        os.makedirs(directory)
    save_path = f'{directory}/{file_name}.png'

    fig, ax = plt.subplots()

    # Set black background
    fig.patch.set_facecolor('black')
    ax.set_facecolor('black')

    # Draw base circles
    for i in range(base_circles):
        circle = patches.Circle((i * 1.5, 0), 0.5, color=base_circle_color)
        ax.add_patch(circle)

    # Draw top circle
    top_circle = patches.Circle(((base_circles - 1) * 0.75, 2), 0.6, color=top_circle_color)
    ax.add_patch(top_circle)

    # Draw lines
    for i in range(base_circles):
        line = plt.Line2D([(i * 1.5), ((base_circles - 1) * 0.75)], [0, 2], color=line_color, linewidth=line_width)
        ax.add_line(line)

    # Set limits and aspect
    ax.set_xlim(-1, base_circles * 1.5)
    ax.set_ylim(-1, 3)
    ax.set_aspect('equal')

    # Remove axes
    ax.axis('off')

    # Save the plot to the specified path
    plt.savefig(save_path, bbox_inches='tight', pad_inches=0, facecolor='black')
    plt.close()

    return save_path

def extract_data_from_discussion(discussion_history: str) -> dict:
    """
    Extracts relevant data from the discussion history for plotting.

    :param discussion_history: The discussion history as a string.
    :return: A dictionary containing extracted data.
    """
    extracted_data = {}

    # Example: Extract number of objectives
    objectives_match = re.findall(r"Objective\s*(\d+):", discussion_history)
    if objectives_match:
        extracted_data["num_objectives"] = len(objectives_match)

    # Add more data extraction patterns here...

    return extracted_data

def generate_parameters_from_data(extracted_data: dict) -> dict:
    """
    Generates diagram parameters based on extracted data.

    :param extracted_data: A dictionary containing extracted data.
    :return: A dictionary containing diagram parameters.
    """
    parameters = {}

    # Example: Map number of objectives to base circles
    if "num_objectives" in extracted_data:
        parameters["base_circles"] = extracted_data["num_objectives"]

    # Add more parameter mappings here...

    return parameters
