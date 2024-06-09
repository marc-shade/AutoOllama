# TeamForgeAI/skills/plot_diagram.py
import streamlit as st
import pandas as pd
import re
from typing import Optional, List, Dict
import json

def plot_diagram(query: Optional[str] = None, discussion_history: str = "") -> str:
    """
    Generates an area chart based on the provided query.

    The query should be a JSON string representing a list of data points, where each data point is a dictionary with 'x' and 'y' values.
    If no query is provided or no valid data points are found in the discussion history, a default query with a single data point (x=0, y=0) will be used.

    For example:
    ```json
    [{"x": 1, "y": 2}, {"x": 2, "y": 5}, {"x": 3, "y": 8}]
    ```

    :param query: A JSON string containing the data points for the chart.
    :param discussion_history: The history of the discussion.
    :return: A JSON string representing the chart data, or an error message if an error occurs.
    """
    try:
        if query is None:
            query = extract_data_points(discussion_history)
            # --- If no valid data points are found, use a default query ---
            if not query:
                query = [{"x": 0, "y": 0}]
        else:
            # --- If a query is provided, try to parse it as JSON ---
            query = json.loads(query)

        # Validate query format
        if not isinstance(query, list):
            raise ValueError("Query must be a list.")
        if not all(isinstance(item, dict) and 'x' in item and 'y' in item for item in query):
            raise ValueError("Each item in the query must be a dictionary with 'x' and 'y' keys.")

        # --- Return the chart data as a JSON string ---
        return json.dumps(query)
    except Exception as e:
        return f"Error: Invalid data format for chart: {e}"  # Return an error message

def extract_data_points(discussion_history: str) -> List[Dict[str, float]]:
    """
    Extracts data points from the discussion history.

    This function attempts to identify potential data points in the discussion history
    by looking for patterns like "x = [value], y = [value]".

    :param discussion_history: The history of the discussion.
    :return: A list of data points, or an empty list if no valid data points are found.
    """
    data_points = []
    pattern = r"x\s*=\s*\[(.*?)\],\s*y\s*=\s*\[(.*?)\]"
    matches = re.findall(pattern, discussion_history)
    for match in matches:
        try:
            x_values = [float(x.strip()) for x in match[0].split(",")]
            y_values = [float(y.strip()) for y in match[1].split(",")]
            if len(x_values) == len(y_values):
                for i in range(len(x_values)):
                    data_points.append({"x": x_values[i], "y": y_values[i]})
        except ValueError:
            pass
    return data_points  # Return the list, even if it's empty

# Example usage in the Streamlit application context
if __name__ == "__main__":
    st.set_page_config(page_title="Chart Plotter", layout="wide")
    st.title("Chart Plotter")

    # Load discussion history from session state or other source
    discussion_history = st.session_state.get("discussion_history", "")

    # Generate and display the chart
    chart_data = plot_diagram(discussion_history=discussion_history)
    if chart_data.startswith("Error:"):
        st.error(chart_data)
    else:
        st.session_state.chart_data = chart_data
        st.rerun()
