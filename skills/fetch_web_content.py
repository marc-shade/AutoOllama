# TeamForgeAI/skills/fetch_web_content.py
import requests
from bs4 import BeautifulSoup
from typing import Optional, List
import re
import streamlit as st

def fetch_web_content(query: str = "", discussion_history: str = "") -> Optional[str]:
    """
    Fetch the content of a webpage and return it as a string.

    If a query is provided, it will fetch content from that specific URL.
    Otherwise, it will analyze the discussion history for URLs and fetch content from those.

    :param query: The URL of the webpage to read.
    :param discussion_history: The history of the discussion.
    :return: The content of the webpage as a string, or None if there is an error.
    """
    urls_to_fetch = []
    if query:
        urls_to_fetch.append(query)
    else:
        # Find URLs in the discussion history
        url_pattern = re.compile(
            r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
        )
        urls_to_fetch = url_pattern.findall(discussion_history)

    if not urls_to_fetch:
        return "Error: No URLs found to fetch content from."

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    all_contents = []
    for url in urls_to_fetch:
        # Check if content from this URL has already been fetched
        if url_content_already_fetched(url, discussion_history):
            continue

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            content = soup.get_text()
            all_contents.append(f"Content from {url}:\n\n{content}\n\n---\n\n")
        except requests.exceptions.Timeout:
            print(f"Error: The request timed out for URL: {url}")
            all_contents.append(f"Error: Could not fetch content from {url} due to timeout.\n\n")
        except requests.exceptions.TooManyRedirects:
            print(f"Error: Too many redirects for URL: {url}")
            all_contents.append(f"Error: Could not fetch content from {url} due to too many redirects.\n\n")
        except requests.exceptions.RequestException as e:
            print(f"Error fetching the webpage content for URL {url}: {e}")
            all_contents.append(f"Error: Could not fetch content from {url} due to an error: {e}\n\n")

    return "".join(all_contents)

def url_content_already_fetched(url: str, discussion_history: str) -> bool:
    """Checks if the content from the given URL has already been fetched in the discussion history."""
    pattern = re.compile(rf"Content from {re.escape(url)}:\n\n(.*?)\n\n---", re.DOTALL)
    return bool(pattern.search(discussion_history))
