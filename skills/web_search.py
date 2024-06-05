# TeamForgeAI/skills/web_search.py
from serpapi import GoogleSearch
import streamlit as st

def web_search(query: str, search_engine: str = "google", result_count: int = 3) -> list:
    """
    Performs a web search using SerpApi and returns the top results.

    Args:
        query (str): The search query string.
        search_engine (str, optional): The search engine to use. Defaults to "google".
        result_count (int, optional): The number of results to return. Defaults to 3.

    Returns:
        list: A list of tuples, where each tuple contains the title, URL, and snippet of a search result.
    """
    discussion_history = st.session_state.get("discussion_history", "")
    search = GoogleSearch({"engine": search_engine, "q": f"{query} {discussion_history[-1000:]}", "api_key": "your_key_goes_here", "num": result_count})
    try:
        results = search.get_dict()
        search_results = []
        for result in results.get("organic_results", []):
            title = result.get("title")
            link = result.get("link")
            snippet = result.get("snippet")
            if title and link and snippet:
                search_results.append((title, link, snippet))
        return search_results
    except Exception as error:
        print(f"Error occurred: {error}")
        return []