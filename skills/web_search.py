# TeamForgeAI/skills/web_search.py
import re
import time
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from typing import List, Tuple
import streamlit as st
import requests
from bs4 import BeautifulSoup
from ollama_llm import OllamaLLM
from autogen.agentchat.contrib.capabilities.teachability import Teachability

MAX_AGENTS = 3  # Limit the number of agents performing searches
MAX_SEARCH_RESULTS = 3  # Limit the number of search results per agent

def web_search(query: str, discussion_history: str = "", agents_data: list = None, teachability=True) -> str:
    """
    Performs a web search using the Google Custom Search API and synthesizes the results using an MoA approach.

    Args:
        query (str): The search query string.
        discussion_history (str, optional): The history of the discussion. Defaults to "".
        agents_data (list, optional): The data of the agents. Defaults to None.
        teachability (Teachability, optional): The agent's teachability object. Defaults to None.

    Returns:
        str: A synthesized summary of the search results.
    """
    # 1. Query Understanding (already handled by the input)

    # 2. Web Crawling and Information Gathering
    search_results = gather_search_results(query, discussion_history, agents_data, teachability)

    # 3. Information Processing and Synthesis
    synthesized_summary = synthesize_search_results(search_results, discussion_history, teachability)

    # 4. Result Generation
    return synthesized_summary

def gather_search_results(query: str, discussion_history: str, agents_data: list, teachability: Teachability, max_retries=3) -> List[Tuple[str, str, str, str, str]]:
    """Gathers search results from the Google Custom Search API for each agent."""
    search_results = []
    for agent in agents_data[:MAX_AGENTS]:  # Limit the number of agents performing searches
        # Refine query using context from Teachability
        refined_query = refine_query_with_teachability(query, teachability, agent)
        service = build("customsearch", "v1", developerKey=st.session_state.google_api_key)
        for attempt in range(max_retries):
            try:
                res = service.cse().list(q=refined_query, cx=st.session_state.search_engine_id, num=MAX_SEARCH_RESULTS).execute()  # Limit the number of search results per agent
                for item in res.get('items', []):
                    title = item.get('title')
                    link = item.get('link')
                    snippet = item.get('snippet')
                    content = fetch_and_clean_content(link)
                    if title and link and snippet and content:
                        search_results.append((agent['config']['name'], title, link, snippet, content))
                break  # Exit the retry loop if successful
            except HttpError as e:
                if e.resp.status in [500, 503]:
                    # Retry for 500 and 503 errors
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    else:
                        raise
                else:
                    raise
    return search_results

def synthesize_search_results(search_results: List[Tuple[str, str, str, str, str]], discussion_history: str, teachability: Teachability) -> str:
    """Synthesizes the search results using an MoA approach."""
    # Proposer Layer: Each agent summarizes its own search results
    proposer_outputs = []
    for agent_name, title, link, snippet, content in search_results:
        proposer_prompt = f"""You are {agent_name}. You have been asked to research the following query: '{title}'. Here is a summary of a web search result: {snippet}\n\n{content}\n\nBased on this information, provide a concise summary of your findings."""
        ollama_llm = OllamaLLM(model="mistral:instruct", temperature=0.4)
        summary = ollama_llm.generate_text(proposer_prompt)
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
    ollama_llm = OllamaLLM(model="mistral:instruct", temperature=0.4)
    synthesized_summary = ollama_llm.generate_text(aggregator_prompt)

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
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        # Check if the response is a text file
        if 'text/plain' in response.headers.get('Content-Type', ''):
            return response.text.strip() # Return raw text content

        soup = BeautifulSoup(response.content, 'html.parser')

        # Remove script and style tags
        for script in soup(["script", "style"]):
            script.decompose()

        # Get text content and clean it
        text = soup.get_text()
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    except Exception as e:
        print(f"Error fetching or cleaning content from {url}: {e}")
        return ""
