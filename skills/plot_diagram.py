# TeamForgeAI/skills/plot_diagram.py
import streamlit as st
import pandas as pd
import json

def plot_diagram(query=None) -> None:
    """
    Generates an area chart based on the provided query.

    The query should be a list of data points, where each data point is a dictionary with 'x' and 'y' values.
    If no query is provided, it will extract data from the discussion history or use default data.

    For example:
    ```json
    [{"x": 1, "y": 2}, {"x": 2, "y": 5}, {"x": 3, "y": 8}]
    ```

    :param query: A list containing the data points for the chart.
    """
    if not query:
        # Extracting data from discussion history
        discussion_history = st.session_state.get("discussion_history", "")
        try:
            # Assuming discussion history is in a specific format containing the plot data
            plot_data_start = discussion_history.find('[')
            plot_data_end = discussion_history.find(']')
            if plot_data_start == -1 or plot_data_end == -1:
                query = [{"x": 0, "y": 0}, {"x": 1, "y": 0}]  # Use default data if no valid plot data found
            else:
                plot_data = discussion_history[plot_data_start:plot_data_end+1]
                query = json.loads(plot_data)
        except json.JSONDecodeError:
            st.error("Error: Invalid discussion history format. Using default data.")
            query = [{"x": 0, "y": 0}, {"x": 1, "y": 0}]
        except ValueError as e:
            st.error(f"Error: {e}. Using default data.")
            query = [{"x": 0, "y": 0}, {"x": 1, "y": 0}]

    try:
        # Validate query format
        if not isinstance(query, list):
            raise ValueError("Query must be a list.")
        if not all(isinstance(item, dict) and 'x' in item and 'y' in item for item in query):
            raise ValueError("Each item in the query must be a dictionary with 'x' and 'y' keys.")
        
        df = pd.DataFrame(query)  # Create DataFrame directly from the list
        st.area_chart(df.set_index('x'))
    except Exception as e:
        st.error(f"Error: Invalid data format for chart: {e}")

# Example usage
example_query = [{"x": 1, "y": 2}, {"x": 2, "y": 5}, {"x": 3, "y": 8}]
