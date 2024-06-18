# TeamForgeAI/search_workflow.py
from autogen.agentchat import GroupChat, GroupChatManager
from ollama_llm import OllamaLLM
from skills.web_search import gather_search_results, synthesize_search_results # Import the functions

def initiate_search_workflow(query: str, create_autogen_agent, OllamaGroupChatManager, update_discussion_and_whiteboard, teachability=True): # Accept teachability
    """Initiates the multi-agent search workflow."""
    # Create agents, passing the teachability object
    search_agent = create_autogen_agent({
        "config": {"name": "Search Agent", "system_message": "You are a helpful search agent."},
        "model": "mistral:7b-instruct-v0.2-fp16",
        "enable_memory": True,
        "db_path": "./db/search_agent"
    }, teachability=teachability) # Pass teachability to create_autogen_agent
    analyst_agent = create_autogen_agent({
        "config": {"name": "Analyst Agent", "system_message": "You are a helpful analyst agent."},
        "model": "mistral:7b-instruct-v0.3-q8_0",
        "enable_memory": True,
        "db_path": "./db/analyst_agent"
    }, teachability=teachability) # Pass teachability to create_autogen_agent
    synthesizer_agent = create_autogen_agent({
        "config": {"name": "Synthesizer Agent", "system_message": "You are a helpful synthesizer agent."},
        "model": "mistral:7b-instruct-v0.3-q8_0",
        "enable_memory": True,
        "db_path": "./db/synthesizer_agent"
    }, teachability=teachability) # Pass teachability to create_autogen_agent

    # Ensure discussion history is retrieved from session state
    discussion_history = st.session_state.get("discussion_history", "")

    # Gather search results
    search_results = gather_search_results(query, discussion_history, [search_agent, analyst_agent, synthesizer_agent], teachability=teachability)

    # Synthesize search results
    synthesized_summary = synthesize_search_results(search_results, discussion_history, teachability)

    # Update discussion history with synthesized summary
    update_discussion_and_whiteboard("Synthesizer Agent", synthesized_summary, "")
