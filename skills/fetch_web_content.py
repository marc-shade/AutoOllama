import requests
from bs4 import BeautifulSoup
from typing import Optional

def fetch_web_content(query: str) -> Optional[str]:
    """
    Fetch the content of a webpage and return it as a string.

    :param query: The URL of the webpage to read.
    :return: The content of the webpage as a string, or None if there is an error.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(query, headers=headers, timeout=10)  # Added timeout and headers
        response.raise_for_status()  # Raise an HTTPError for bad responses
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup.get_text()
    except requests.exceptions.Timeout:
        print("Error: The request timed out.")
        return None
    except requests.exceptions.TooManyRedirects:
        print("Error: Too many redirects.")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the webpage content: {e}")
        return None

# Example usage
if __name__ == "__main__":
    url = "https://2acrestudios.com/"
    content = fetch_web_content(query=url)
    if content:
        print(content)
    else:
        print("Failed to retrieve content.")
