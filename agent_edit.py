# TeamForgeAI/ui/virtual_office.py

import os
import base64
import streamlit as st
import random

# --- Function to format markdown with background image ---
def background_markdown(background_image: str) -> str:
    """Returns a Markdown string with embedded CSS for styling the virtual office."""
    return f"""
    <style>
    :root {{
        --primary-color: #007bff; /* Blue */
        --secondary-color: #dc3545; /* Red */
        --text-color: #000; /* Black for light mode */
        --background-color: #FFF; /* White */
        --sidebar-background-color: #FFF; /* White */
        --virtual-office-overlay: transparent; /* Default to transparent */
    }}

    /* Override colors in dark mode */
    @media (prefers-color-scheme: dark) {{
        :root {{
            --text-color: #eee; /* Light grey for dark mode */
            --background-color: #333; /* Dark grey */
            --sidebar-background-color: #444; /* Darker grey */
            --virtual-office-overlay: rgba(0, 0, 0, 0.5); /* Dark overlay for dark mode */
        }}
    }}

    /* General styles */
    body {{
        font-family: 'Courier New', sans-serif!important;
        background-color: var(--background-color);
        font-family: Helvetica, Arial !important;
        color: black!important; /* Set default font color to black for light mode */
    }}

    h1 {{
        font-size: 40px !important;
        color: #FFF!important;
        font-family: Helvetica, Arial !important;
    }}
    
    h2 {{
        font-size: 16px !important;
        color: var(--text-color)!important;
        font-family: Helvetica, Arial !important;
    }}

    /* Sidebar styles */
    .css-1d391kg, .css-1d391kg .css-fblp2m {{
        background-color: var(--sidebar-background-color) !important;
        padding: 0px !important;
        border-radius: 5px !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1) !important;
        font-family: Helvetica, Arial !important;
    }}

    .css-1d391kg h1, .css-1d391kg h2 {{
        color: var(--text-color) !important;
    }}
    
    .logo {{
        font-size: 50px !important;
        color: red!important;
    }}
    .sidebar .stButton button {{
        display: block !important;
        width: 100% !important;
        padding: 10px 0px !important; /* Added padding for better look */
        background-color: var(--primary-color) !important;
        color: #ffffff !important;
        text-align: center !important;
        text-decoration: none !important;
        border-radius: 5px !important;
        transition: background-color 0.3s !important;
    }}
    .sidebar .stButton button:hover {{
        background-color: #0056b3 !important; /* Darker blue on hover */
    }}
    .sidebar a {{
        display: block !important;
        color: var(--primary-color) !important;
        text-decoration: none !important;
    }}
    .sidebar a:hover {{
        text-decoration: underline !important;
    }}

    /* Main content styles */
    .main .stTextInput input {{
        width: 100% !important;
        padding: 10px !important;
        border: 1px solid #cccccc !important;
        border-radius: 5px !important;
        font-family: 'Courier New', sans-serif!important;
    }}
    .main .stTextArea textarea {{
        width: 100% !important;
        padding: 10px !important;
        border: 1px solid #cccccc !important;
        border-radius: 5px !important;
        resize: none !important;
        font-family: 'Courier New', sans-serif!important;
    }}
    button {{
        padding: 8px !important;
        color: #ffffff;
        cursor: pointer !important;
        margin: 0!important;
    }}
    .main .stButton button {{
        padding: 10px 20px !important; /* Adjusted padding */
        background-color: var(--secondary-color) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 5px !important;
        cursor: pointer !important;
        transition: background-color 0.3s !important;
    }}
    .main .stButton button:hover {{
        background-color: #c82333 !important; /* Darker red on hover */
    }}

    div.stTabs .stButton button, 
    div.stTabs .stButton button:hover {{
        background-color: transparent!important;
    }}

    /* Model selection styles */
    .main .stSelectbox select {{
        width: 100% !important;
        padding: 3px !important;
        border: 1px solid #cccccc !important;
        border-radius: 5px !important;
        font-family: 'Open Sans'!important;
    }}

    /* Error message styles */
    .main .stAlert {{
        color: var(--text-color) !important;
    }}

    /* Virtual Office Styles */
    .virtual-office {{
        width: 100%;
        height: 330px; /* Corrected height to 330px */
        border: 1px solid #ccc;
        position: relative;
        overflow: hidden;
        background-image: url('data:image/png;base64,{background_image}'); /* Apply background image here */
        background-size: cover;
        background-position: center;
        background-color: var(--virtual-office-overlay); /* Use the overlay variable here */
    }}

    /* Apply background image to ::before pseudo-element */
    .virtual-office::before {{
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-image: url('data:image/png;base64,{background_image}');
        background-size: cover;
        background-position: center;
        z-index: 1;
    }}


    /* Light mode styles */
    @media (prefers-color-scheme: light) {{
        .virtual-office {{
            background: rgba(0, 0, 0, 0); /* Apply dark overlay only in dark mode */
        }}
    }}

    /* Dark mode styles */
    @media (prefers-color-scheme: dark) {{
        .virtual-office {{
            background: rgba(0, 0, 0, 0.5); /* Apply dark overlay only in dark mode */
        }}
    }}

    .agent-emoji {{
        font-size: 40px; /* Default size */
        position: absolute;
        transition: left 1s, top 1s, font-size 0.5s; /* Adjust animation duration */
        filter: brightness(0.8); /* Adjust the brightness value as needed */
        z-index: 2;
    }}
    .agent-emoji.active {{
        font-size: 80px;
        filter: brightness(1.1); /* Adjust the brightness value as needed */
    }}

    /* Speech Bubble Styles */
    .speech-bubble {{
        position: absolute;
        background-color: #333;
        color: #ccc;
        border-radius: 11px;
        padding: 6px;
        font-size: 16px!important;
        font-weight: light!important;
        font-family: 'Courier New', sans-serif!important;
        margin-top: 16px;
        margin-left: 20px;
        display: none;
        z-index: 3;
    }}
    .speech-bubble p, 
    .speech-bubble li {{
        font-size: 11px!important;
        line-height: 100%;
    }}
    
    .agent-emoji.active + .speech-bubble {{
        display: block; /* Show only for active agent */
    }}

    /* Ensuring minimum height for the Virtual Office column */
    .virtual-office-column {{
        display: flex;
        flex-direction: column;
        justify-content: center;
    }}
    </style>
    """

def display_virtual_office(background_image: str) -> None:
    """Displays the virtual office with animated emojis."""
    agents_data = st.session_state.get("agents_data", [])
    active_agent_name = st.session_state.get("next_agent", None)  # Get the active agent
    last_comment = st.session_state.get("last_comment", "")[:400]  # Get the last comment (first X number of characters)

    office_html = """
    <div class="virtual-office">
        {}  
    </div>
    """

    agent_emojis = ""
    # Only create emojis if there are agents in agents_data
    if agents_data:
        for i, agent_data in enumerate(agents_data):
            agent_name = agent_data["config"].get("name", f"Agent {i+1}")
            agent_emoji = agent_data.get("emoji")

            # Skip agents without an emoji
            if not agent_emoji:
                continue

            # Apply active class if the agent is the active agent
            active_class = "active" if agent_name == active_agent_name else ""

            if agent_name == active_agent_name:
                # Active agent at the top
                left_pos = 130  # Centered horizontally
                top_pos = 20
            else:
                # Other agents mill around below - Adjusted vertical range
                left_pos = random.randint(10, 250)
                top_pos = random.randint(120, 270)  

            agent_emojis += f'<span id="agent-{i}" class="agent-emoji {active_class}" style="left: {left_pos}px; top: {top_pos}px;">{agent_emoji}</span>'
            # Add speech bubble for the active agent with the last comment and '...'
            if active_class:
                agent_emojis += f'<div class="speech-bubble" style="left: {left_pos + 80}px; top: {top_pos - 30}px;">{last_comment}...</div>'

    # --- Call markdown before the office_html ---
    st.markdown(background_markdown(background_image), unsafe_allow_html=True)
    st.markdown(office_html.format(agent_emojis), unsafe_allow_html=True)

    # --- Move JavaScript for animation after the virtual office HTML ---
    animation_script = """
    <script>
    function animateAgents() {
        const agents = document.querySelectorAll('.agent-emoji');
        const activeAgent = '""" + (active_agent_name.replace(" ", "_") if active_agent_name else "") + """'; 

        agents.forEach(agent => {
            if (agent.id.includes(activeAgent)) return; // Don't animate the active agent

            const leftPos = Math.random() * (250 - 10) + 10;
            const topPos = Math.random() * (270 - 160) + 120; // Adjust vertical range
            agent.style.left = leftPos + 'px';
            agent.style.top = topPos + 'px';
        });
    }
    setInterval(animateAgents, 1000); // Adjust animation interval
    </script>
    """

    st.markdown(animation_script, unsafe_allow_html=True)


@st.cache_resource
def load_background_images(folder_path: str, cache_key=None) -> str:
    """Loads background images from the specified folder and returns a random one."""
    background_images = []
    for filename in os.listdir(folder_path):
        if filename.endswith((".png", ".jpg", ".jpeg")):
            image_path = os.path.join(folder_path, filename)
            background_images.append(image_path)
    if background_images:
        return random.choice(background_images) # Randomly choose a background image path
    else:
        return None # Return None if no images are found
