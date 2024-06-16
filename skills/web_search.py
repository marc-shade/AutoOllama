# TeamForgeAI/skills/web_search.py
import re
import time
import logging
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from typing import List, Tuple
import streamlit as st
import requests
from bs4 import BeautifulSoup
from ollama_llm import OllamaLLM
from autogen.agentchat.contrib.capabilities.teachability import Teachability

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

MAX_AGENTS = 3  # Limit the number of agents performing searches
MAX_SEARCH_RESULTS = 3  # Limit the number of search results per agent
MAX_RETRIES = 3  # Maximum number of retries for server errors
REQUEST_TIMEOUT = 10  # Timeout for web requests

def web_search(query: str, discussion_history: str = "", agents_data: list = None, teachability=None) -> str:
    """
    Performs a web search using the Google Custom Search API and synthesizes the results using an MoA approach.

    Args:
        query (str): The search query string.
        discussion_history (str, optional): The history of the discussion. Defaults to "".
        agents_data (list, optional): The data of the agents. Defaults to None.
        teachability (Teachability, optional): The agent's teachability object. Defaults to None.

    Returns:
        str: A synthesized summary of the search results, or an error message if an error occurs.
    """
    try:
        logging.info(f"Starting web search for query: {query}")

        # 1. Query Understanding (already handled by the input)

        # 2. Web Crawling and Information Gathering
        logging.info("Gathering search results...")
        search_results = gather_search_results(query, discussion_history, agents_data, teachability)
        logging.info(f"Gathered {len(search_results)} search results.")

        # 3. Information Processing and Synthesis
        logging.info("Synthesizing search results...")
        synthesized_summary = synthesize_search_results(search_results, discussion_history, teachability)
        logging.info("Search results synthesized.")

        # 4. Result Generation
        logging.info("Web search completed.")
        return synthesized_summary
    except Exception as e:
        logging.error(f"Error during web search: {e}")
        return f"Error during web search: {e}"

def gather_search_results(query: str, discussion_history: str, agents_data: list, teachability: Teachability) -> List[Tuple[str, str, str, str, str]]:
    """Gathers search results from the Google Custom Search API for each agent."""
    search_results = []
    for i, agent in enumerate(agents_data[:MAX_AGENTS]):  # Limit the number of agents performing searches
        logging.info(f"Gathering search results for agent {i+1}: {agent['config']['name']}")
        # Refine query using context from Teachability
        refined_query = refine_query_with_teachability(query, teachability, agent)
        logging.info(f"Refined query: {refined_query}")
        service = build("customsearch", "v1", developerKey=st.session_state.google_api_key)
        for attempt in range(MAX_RETRIES):
            try:
                res = service.cse().list(q=refined_query, cx=st.session_state.search_engine_id, num=MAX_SEARCH_RESULTS).execute()  # Limit the number of search results per agent
                logging.info(f"Google Search API response: {res}")
                for item in res.get('items', []):
                    title = item.get('title')
                    link = item.get('link')
                    snippet = item.get('snippet')
                    logging.info(f"Fetching content from: {link}")
                    content = fetch_and_clean_content(link)
                    if title and link and snippet and content:
                        search_results.append((agent['config']['name'], title, link, snippet, content))
                break  # Exit the retry loop if successful
            except HttpError as e:
                if e.resp.status in [500, 503] and attempt < MAX_RETRIES - 1:
                    logging.warning(f"Retrying due to server error ({e.resp.status}): {e.content}")
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                else:
                    logging.error(f"Error during Google Search: {e}")
                    break # Break on any other error or after max retries
            except Exception as e:
                logging.error(f"Unexpected error: {e}")
                break
    return search_results

def synthesize_search_results(search_results: List[Tuple[str, str, str, str, str]], discussion_history: str, teachability: Teachability) -> str:
    """Synthesizes the search results using an MoA approach."""
    # Proposer Layer: Each agent summarizes its own search results
    proposer_outputs = []
    for i, (agent_name, title, link, snippet, content) in enumerate(search_results):
        logging.info(f"Synthesizing result {i+1} for agent: {agent_name}")
        proposer_prompt = f"""You are {agent_name}. You have been asked to research the following query: '{title}'. Here is a summary of a web search result: {snippet}\n\n{content}\n\nBased on this information, provide a concise summary of your findings."""
        logging.info(f"Proposer prompt: {proposer_prompt}")
        ollama_llm = OllamaLLM(model="mistral:instruct", temperature=0.4)
        summary = ollama_llm.generate_text(proposer_prompt)
        logging.info(f"Proposer summary: {summary}")
        proposer_outputs.append((agent_name, summary, link)) # Include link for sources

    # Aggregator Layer: Combine the summaries from the proposers
    memories = teachability.get_memories(k=5) if isinstance(teachability, Teachability) else []
    memory_content = " ".join([m['content'] for m in memories])
    aggregator_prompt = f"""You are the Editor. You have been provided with summaries from different agents on a research topic. Your task is to synthesize these summaries into a single, coherent report, considering the conversation history.

    Conversation History:
    {discussion_history}

    Memory Content:
    {memory_content}

    Agent Summaries:
    {chr(10).join([f'- {agent_name}: {summary}' for agent_name, summary, _ in proposer_outputs])}
    """
    logging.info(f"Aggregator prompt: {aggregator_prompt}")
    ollama_llm = OllamaLLM(model="mistral:instruct", temperature=0.4)
    synthesized_summary = ollama_llm.generate_text(aggregator_prompt)
    logging.info(f"Synthesized summary: {synthesized_summary}")

    # Add Sources section
    sources = "\n\n## Sources:\n" + chr(10).join([f"- [{title}]({link})" for _, title, link, _, _ in search_results])
    synthesized_summary += sources

    return synthesized_summary

def refine_query_with_teachability(query: str, teachability: Teachability, agent: dict) -> str:
    """Refines the search query using context from the agent's memory."""
    memories = teachability.get_memories(k=5) if isinstance(teachability, Teachability) else []
    relevant_info = " ".join([m['content'] for m in memories])
    refined_query = f"{query} {agent['description']} {relevant_info}"
    return refined_query

def search_result_already_returned(title: str, link: str, snippet: str, discussion_history: str) -> bool:
    """Checks if the given search result has already been returned in the discussion history."""
    pattern = re.compile(rf"- {re.escape(title)}: {re.escape(link)} \({re.escape(snippet)}\)", re.DOTALL)
    return bool(pattern.search(discussion_history))

def fetch_and_clean_content(url: str) -> str:
    """Fetches content from a given URL and cleans it using BeautifulSoup."""
    try:
        logging.info(f"Fetching content from: {url}")
        response = requests.get(url, timeout=REQUEST_TIMEOUT) # Add timeout to requests.get
        response.raise_for_status()

        # Check if the response is a text file
        if 'text/plain' in response.headers.get('Content-Type', ''):
            logging.info(f"Content is plain text.")
            return response.text.strip() # Return raw text content

        soup = BeautifulSoup(response.content, 'html.parser')

        # Remove script and style tags
        for script in soup(["script", "style"]):
            script.decompose()

        # Get text content and clean it
        text = soup.get_text()
        text = re.sub(r'\s+', ' ', text).strip()
        logging.info(f"Content fetched and cleaned.")
        return text
    except Exception as e:
        logging.error(f"Error fetching or cleaning content from {url}: {e}")
        return ""
