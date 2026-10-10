# Medical AI Triage - Real-time Conversational Voice Bot 

> #### IMPORTANT: Inframedica API services won't be working as it was only given access for limited period of time for testing the service - reachout to Inframedica to get access of the API key.

> #### [Agent Demo](./resources/voice_agent_demo.mp3) <br> The demo is a `.mp3` file you need to download to check the agent in action.

> #### ACE Internship Completion [CERTIFICATE](./CERTIFICATE.pdf)

> *NOTE: This project started from June till the end of July 2025 and was delivered and handed over on 30th June 2025.*

## Overview

This project is a proof-of-concept real-time conversational voice agent for GP front-desk triage. It uses natural-language conversation to collect patient symptoms, run a structured diagnosis interview through the Inframedica Engine API, support appointment and general GP enquiries, and store relevant information through a FastAPI backend.

The system was built with Pipecat, an LLM-based conversation flow, tool calling, and a FastAPI backend, then deployed on Cerebrium. It demonstrates that an AI voice agent can automate parts of GP front-desk workflows while escalating urgent or complex cases appropriately.

## System Design & Flows

The following documents describe how the voice agent manages conversations, interacts with backend services, and stores GP front-desk data.

- [Conversation Flow](./resources/Conversation%20Flow.pdf): High-level state flow showing how the voice agent handles emergency, clinical, booking, and general-information scenarios.
- [Database Design](./resources/GP%20Frontdesk%20ERD.html): ERD for the GP front-desk backend, showing the main data entities and their relationships.
- [System Workflow](./resources/System%20Workflow.pdf): End-to-end pipeline showing how user speech is transcribed, processed by the LLM, used for tool calls, and converted back into speech.

## Getting started

- Setup WSL in your windows if your are using windows or if you are in linux distro then you can skip this step (reason for WSL is becuse the `pipecat` framework internal dependency `daily-python` is not yet available in windows environment).
- Configure all fields in `.env` files for both bot and backend (gather all api keys and configs values).
- Create ` python -m venv .venv` and start the isolated development environment `source .venv/bin/activate` to seperate the project dependency from the global dependency.
- Then run `pip install -r requirements.txt` to install all required dependencies for the project.
- Now start the backend server `python ./backend/main.py` (Any issues and troubleshooting regarding backend service reach out to [Joshep](https://github.com/AdebisiJoe) who has developed the backend service). 
- Now you are ready to run the voice bot run `python main.py`.

> NOTE: Postman API collections exports are available in the `/postman-api-exports` directory which includes the env file and collections of APIs for backend service and Inframedica.

## Project Status

This repository contains a working proof of concept, not a production-ready medical system.

### Delivered

- [x] Real-time voice interaction using speech-to-text, LLM reasoning, and text-to-speech.
- [x] Natural-language symptom collection and structured diagnosis interviews through the Inframedica Engine API.
- [x] Conversation flows for emergency escalation, clinical triage, appointment booking, and general GP enquiries.
- [x] FastAPI backend integration for storing and retrieving GP front-desk data.
- [x] Deployment of both the voice agent and backend service on Cerebrium.

### Outcome

The prototype validated the core idea: an AI voice agent can support GP front-desk triage and administrative workflows. It provides a practical foundation for a more robust, secure, and production-oriented implementation.

## Development Notes

This was a time-boxed internship prototype. Parts of the implementation were accelerated using AI-assisted development tools, with the overall system design, integration, testing, debugging, and deployment carried out as part of the project delivery.

The codebase is intended as a reference implementation rather than production software.


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
