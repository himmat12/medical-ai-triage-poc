# Medical AI Triage Conversational Voice Bot 

> #### IMPORTANT: Inframedica API services won't be working as it was only given access for limited period of time for testing the service - reachout to Inframedica to get access of the API key.

> #### [Agent Demo](./resources/voice_agent_demo.mp3)
The demo is a `.mp3` file you need to download to check the agent in action.


## Getting started

- Setup WSL in your windows if your are using windows or if you are in linux distro then you can skip this step (reason for WSL is becuse the `pipecat` framework internal dependency `daily-python` is not yet available in windows environment).
- Configure all fields in `.env` files for both bot and backend (gather all api keys and configs values).
- Create ` python -m venv .venv` and start the isolated development environment `source .venv/bin/activate` to seperate the project dependency from the global dependency.
- Then run `pip install -r requirements.txt` to install all required dependencies for the project.
- Now start the backend server `python ./backend/main.py` (Any issues and troubleshooting regarding backend service reach out to [Joshep](https://github.com/AdebisiJoe) who has developed the backend service). 
- Now you are ready to run the voice bot run `python main.py`.

> NOTE: Postman API collections exports are available in the `/postman-api-exports` directory which includes the env file and collections of APIs for backend service and Inframedica.

## Project Status:

#### Current progress
The current status or progress of the project is just a simple proof-of-concept implementation to validate the idea which includes:

- [x] Bot can be able to speak and understand natural language.
- [x] Bot can be able to take symptoms and run diagnosis interview by leveraging `Inframedica Engine API`.
- [x] Bot can access the database and maupulate (CRUD) database to store and retrive information.
- [x] Deployed in cerebrium both backend service and voice bot service.

In conclusion the basic foundation of the project has been setup and done - what it means is Dr. Shafiq vision and conceptual ideas about automating the front desk of GP and optimizing the primary health care sector workflow works in practical as during this project we have acheieved all of the above conditions through this proof of concept voice bot.


#### What next?
This code samples are not the final and refined version of the voice bot imlementation and some codes are generated with the help of AI tools (cursor / calude) just to build the working prototype and is not ready for production or not even near production. This is barely scratching the surface of this ambitious project.

Next steps would be understanding the fundamental system design and architecture and implementing it properly into new project by taking this proof of concept as reference.


## Things to consider:

- LLM Context management or optimisation (context engineering) - as this voice bot implementation does not handle the context, which means no any context engineering has been implemented. But this optimisation is mandatory for production to reduce inference latency and token generation.

- Replacing the LLM service by self hosted finetuned LLM model in cerebrium or any other cloud platform alternatives to reduce costs and mainly Latency.


## Useful resources:

[Pipecat voicebot implementation examples](https://github.com/pipecat-ai/pipecat-examples) - While developing this bot in pipecat I have followed along these examples and hope you will find this helpful.

[Cerebrium deployment of Real-time Voice Agent example](https://docs.cerebrium.ai/v4/examples/realtime-voice-agents) - This will be a really good starting point to understand how voice bot build in `pipecat` are deployed in the cerebrium platform.

[Voice bot conversation flow](./resources/Conversation%20Flow.pdf) - In order to manage the conversation flow (conversation state) of voice bot I have used `pipecat-flow` framework and this flowchart clearly illustrates the high level picture of how bot transitions into different conversation nodes.

[System workflow](./resources/System%20Workflow.pdf) - This illustration will give you a clear picture of system input and output workflow like how the bot process user input (speech) -> transcribes to text -> NLP (understands the natural human language) -> takes actions (tool calls/retrival/agentic actions if required) -> transcribes text to speech -> and produce speech output (responds/speaks) through out different layers.

[GP Front Desk database design - DB ERD](./resources/GP%20Frontdesk%20ERD.html) - This is a database design of our backend service build on FastAPI.

[Postman API collection exports](./postman-api-exports/) - All the API collections of `Inframedica` and `GP Front Desk` system (FastAPI backend & Voice bot) are available here, import and test the deployed backend service and voice bot endpoints.

[Visualizing bot debug logs](./client/gp_front_desk_web_app/) - To visualize the bot debug logs use this simple web interface where you can see conversation history along with function calls and function call responses and the all information logged as debug logs. In order to visualize simply copy the full LLM input JSON from the debug console and paste it in the input field and analyse it.
