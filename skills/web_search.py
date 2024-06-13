# TeamForgeAI/skills/web_search.py
import re
from serpapi.google_search_results import GoogleSearch  # Updated import
import streamlit as st

def web_search(query: str, search_engine: str = "google", result_count: int = 3, discussion_history: str = "") -> list:
    """
    Performs a web search using SerpApi and returns the top results.

    Args:
        query (str): The search query string.
        search_engine (str, optional): The search engine to use. Defaults to "google".
        result_count (int, optional): The number of results to return. Defaults to 3.
        discussion_history (str, optional): The history of the discussion. Defaults to "".

    Returns:
        list: A list of tuples, where each tuple contains the title, URL, and snippet of a search result.
    """
    full_query = f"{query} {discussion_history[-1000:]}"
    search = GoogleSearch({
        "engine": search_engine,
        "q": full_query,
        "api_key": "your_key_goes_here",
        "num": result_count
    })
    
    try:
        results = search.get_dict()
        search_results = []
        for result in results.get("organic_results", []):
            title = result.get("title")
            link = result.get("link")
            snippet = result.get("snippet")
            if title and link and snippet:
                # Check if this search result has already been returned
                if not search_result_already_returned(title, link, snippet, discussion_history):
                    search_results.append((title, link, snippet))
        return search_results
    except Exception as error:
        print(f"Error occurred: {error}")
        return []

def search_result_already_returned(title: str, link: str, snippet: str, discussion_history: str) -> bool:
    """Checks if the given search result has already been returned in the discussion history."""
    pattern = re.compile(rf"- {re.escape(title)}: {re.escape(link)} \({re.escape(snippet)}\)", re.DOTALL)
    return bool(pattern.search(discussion_history))
