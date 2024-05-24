# TeamForgeAI/skills/web_search.py
from serpapi import GoogleSearch

def web_search(query: str, search_engine: str = "google", result_count: int = 3):
    """
    Performs a web search using SerpApi and returns the top results.

    Args:
        query (str): The search query string.
        search_engine (str, optional): The search engine to use. Defaults to "google".
        result_count (int, optional): The number of results to return. Defaults to 3.

    Returns:
        list: A list of tuples, where each tuple contains the title, URL, and snippet of a search result.
    """
    params = {
        "engine": search_engine,
        "q": query,
        "api_key": "0bcdb5f122047552b3f0e8b22591f77299eb541008be5a5cbea46157bbc2bc46", # Replace with your actual SerpApi key
        "num": result_count, # Number of results to retrieve
    }

    print(f"SerpApi parameters: {params}") # Log the parameters being sent to SerpApi
    search = GoogleSearch(params)
    results = search.get_dict()

    print(f"SerpApi raw results: {results}") # Log the raw results from SerpApi

    search_results = []
    for result in results.get("organic_results", []):
        title = result.get("title")
        link = result.get("link")
        snippet = result.get("snippet")
        if title and link and snippet:
            search_results.append((title, link, snippet))

    return search_results