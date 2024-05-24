<h1 style="color: red;">🦊🐻🐹 Team<span style="color: orange;">Forge</span><span style="color: yellow;">AI</span></h1>


## AI Agent Collaboration Platform

**TeamForgeAI** is a platform designed for creating, managing, and collaborating with AI agents. Built using Streamlit, this application allows you to define agents with specific skills and expertise, and then engage them in a group chat setting to solve tasks collaboratively.

<img src="https://2acrestudios.com/wp-content/uploads/2024/05/Screenshot-2024-05-24-at-6.48.27 AM.png" />


## Features

<img src ="https://2acrestudios.com/wp-content/uploads/2024/05/00016-1652154937.png" align="right" style="width: 300px;" />

- **Agent Creation**: Design custom AI agents with unique names, descriptions, skills, and tools.
- **Skill Integration**: Integrate custom Python skills that agents can utilize during interactions.
- **Team Management**: Organize agents into teams for better project management.
- **Collaborative Workflow**: Engage agents in a group chat, facilitating collaborative problem-solving.
- **Discussion History**: Maintain a record of all agent interactions for reference and analysis.
- **Code Generation and Execution**: Agents can generate and execute code snippets within the chat.
- **File Download**: Download agent configurations and workflows for easy sharing and deployment.

## Installation

Clone the repository:
```bash
git clone https://github.com/your-username/TeamForgeAI.git
cd TeamForgeAI
```

Install dependencies:
```bash
pip install -r requirements.txt
```

Start the application:
```bash
streamlit run main.py
```

## Usage

<img src="https://2acrestudios.com/wp-content/uploads/2024/05/grid-0006.png" align="right" style="width: 300px;" />

**Create Agents:**
- Use the sidebar to define new agents.
- Provide a name, description, select skills, and list tools for each agent.

**Organize Teams:**
- Create teams to group agents based on projects or tasks.
- Save agents into teams

**Start a Discussion:**
- Input your request or problem statement in the main input area, 'Enter your request.'
- The application will rephrase the request into an optimized prompt and automatically generate the agents to complete the task!
- Add any 'Additional Input' if you need to add to interject in the team's discussion

**Interact with Agents:**
- Click on an agent's button to trigger their response.
- Agents will communicate and collaborate within the discussion area.
- Customize each agent's settings.
- Refine the agent's prompts dynamically based on the Discussion History context.

**Skills:**

<img src ="https://2acrestudios.com/wp-content/uploads/2024/05/00017-1652154938.png" align="right" style="width: 300px;" />

The skills are implemented using a 'sure-shot' method, guaranteeing they will trigger without relying solely on an AI prompt. The skills are assigned to an agent, effectively switching them into a sort of 'tools mode' that mandates that they use the tool as a programmatic response. This avoids issues often seen in group chat situations where an agent hallucinates and pretends to run the skill script. When you push the agent button in TeamForgeAI, the agent will always use the skill.
- 'Web Search' uses Serper and you must provide your API for this skill to function
- 'Fetch Web Content' reads the content of a web page into the conversation
- 'Generate SD Images' creates an image based on the conversation context

**Review and Download:**
- The discussion history is preserved for future reference.
- Download agent configurations and workflows as needed.

## Contributing

We welcome contributions to enhance TeamForgeAI's capabilities. To contribute:
1. Fork the repository.
2. Create a new branch for your feature.
3. Implement your changes and ensure they are well-documented.
4. Submit a pull request for review.

## License

This project is licensed under the MIT License. See the LICENSE file for details.

