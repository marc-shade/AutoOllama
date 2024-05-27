<h1 style="color: red;">🦊🐻🐹 Team<span style="color: orange;">Forge</span><span style="color: yellow;">AI</span></h1>


## AI Agent Collaboration Platform

**TeamForgeAI** is a platform designed for creating, managing, and collaborating with AI agents. Built using Streamlit, this application allows you to define agents with specific skills and expertise, and then engage them in a group chat setting to solve tasks collaboratively.

<img src="https://2acrestudios.com/wp-content/uploads/2024/05/Screenshot-2024-05-27-at-6.43.26 AM.png" />


## Features

<img src ="https://2acrestudios.com/wp-content/uploads/2024/05/00016-1652154937.png" align="right" style="width: 300px;" />

- **AI-Powered Agent Creation:** Generate specialized AI agents based on your project description. Each agent possesses unique skills and tools tailored to their role.
- **Collaborative Workflow:** Agents interact and collaborate to solve problems, generate ideas, and complete tasks.
- **Project Goal, Objectives, and Deliverables:** Define and track your project's overall goal, specific objectives, and tangible deliverables.
- **Skill Integration:** Integrate custom Python skills to extend agent capabilities and automate tasks.
- **Web Search and Content Summarization:** Agents can perform web searches and summarize content from provided URLs.
- **Image Generation:** Generate images using Stable Diffusion, powered by the Automatic1111 API.
- **Interactive Discussion and Whiteboard:** Track agent interactions, share ideas, and store code snippets on a virtual whiteboard.
- **Downloadable Agent and Workflow Files:** Export agents and workflows as JSON files for use in AutoGen and CrewAI.
- **Team Management:** Create and manage teams of agents, allowing for flexible collaboration and organization.
- **Visual Virtual Office:** An engaging virtual office with animated emojis representing each agent, providing a fun and intuitive way to visualize agent interactions.


## Installation

Clone the repository:
```bash
git clone https://github.com/your-username/TeamForgeAI.git
cd TeamForgeAI
```

Create virtual environment:
```bash
conda create --name teamforge python=3.11
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
- 'Web Search' uses Serper, and you must provide your API for this skill to function
- 'Fetch Web Content' reads the content of a web page into the conversation
- 'Generate SD Images' creates an image based on the conversation context
- 'Project Management' empowers an agent with the ability to manage projects and provide status updates to the team.

TeamForgeAI supports custom Python skills that can be integrated into agents. To create a new skill:
1. Create a new Python file in the skills directory.
2. Define a function with the same name as the skill.
3. Add a docstring to describe the skill's functionality.
4. Save the file with a .py extension.
5. The skill will be automatically loaded and available for assignment to agents.

**Review and Download:**
- The discussion history is preserved for future reference.
- Download agent configurations and workflows as needed.

Examples: 
- Write a children's book: Request TeamForgeAI to create a children's book about a llama. Agents such as a "Children's Book Writer", "Illustrator", and "Language Specialist" will be generated to collaborate on the project.
- Develop a marketing plan: Ask TeamForgeAI to develop a marketing plan for a new product. Agents like a "Market Research Analyst", "Content Creator", and "Social Media Manager" will work together to create a comprehensive plan.
- Build a website: Request TeamForgeAI to build a website for your business. Agents such as a "Web Developer", "Designer", and "Content Writer" will collaborate to bring your website to life.

## Contributing

We welcome contributions to enhance TeamForgeAI's capabilities. To contribute:
1. Fork the repository.
2. Create a new branch for your feature.
3. Implement your changes and ensure they are well-documented.
4. Submit a pull request for review.

## License

This project is licensed under the MIT License. Portions of this code are derived from [AutoGroq by J. Gravelle](https://github.com/jgravelle/AutoGroq).

MIT License

Copyright (c) 2024 Marc Shade

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

