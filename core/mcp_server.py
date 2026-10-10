"""
MCP Server for GP Voice Agent Tools
"""

import asyncio
import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import uuid4

import requests
from dotenv import load_dotenv
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from mcp.server import Server

from loguru import logger

load_dotenv(override=True)

# Global state
evidence_list: List[Dict[str, str]] = []
evidence_set: set = set()
patient_data_cache: Optional[Dict[str, Any]] = None
patient_id: int
call_id: int

# Infermedica API configuration
base_url = os.environ.get("INFRAMEDICA_BASE_URL")
app_id = os.environ.get("INFRAMEDICA_APP_ID")
app_key = os.environ.get("INFRAMEDICA_APP_KEY")
interview_id: Optional[str] = None

# Backend service API configuration
backend_base_url = os.environ.get("BACKEND_BASE_URL")
backend_api_router = os.environ.get("BACKEND_API_ROUTER")
username = os.environ.get("USERNAME")
password = os.environ.get("PASSWORD")
access_token = os.environ.get("ACCESS_TOKEN")

if not app_id or not app_key:
    logger.error(
        "Missing required environment variables: INFRAMEDICA_APP_ID or INFRAMEDICA_APP_KEY"
    )
    # raise ValueError(
    #     "Missing required environment variables: INFRAMEDICA_APP_ID or INFRAMEDICA_APP_KEY"
    # )

if not backend_base_url or not username or not password or not access_token:
    logger.error(
        "Missing required environment variables: BACKEND_BASE_URL or USERNAME or PASSWORD or ACCESS_TOKEN"
    )
    # raise ValueError(
    #     "Missing required environment variables: BACKEND_BASE_URL or USERNAME or PASSWORD or ACCESS_TOKEN"
    # )

# Create MCP server instance
server = Server("gp-voice-agent-tools")


@server.list_tools()
async def list_tools() -> List[Tool]:
    """List all available tools"""
    try:
        tools = [
            # parse_text
            Tool(
                name="parse_text",
                description="NLP service for parsing natural text from patients to identify medical concepts",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "Patient's natural language input",
                        },
                        "age": {"type": "integer", "description": "Patient's age"},
                        "sex": {
                            "type": "string",
                            "description": "Patient's biological sex (male/female)",
                        },
                    },
                    "required": ["text", "age", "sex"],
                },
            ),
            # suggest
            Tool(
                name="suggest",
                description="Method to refine the initial observation (symptoms, and conditions)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "age": {"type": "integer", "description": "Patient's age"},
                        "sex": {
                            "type": "string",
                            "description": "Patient's biological sex",
                        },
                        "evidence": {
                            "type": "array",
                            "description": "List of evidence objects",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "string"},
                                    "choice_id": {
                                        "type": "string",
                                        "enum": ["present", "absent", "unknown"],
                                    },
                                    "source": {"type": "string"},
                                },
                                "required": ["id", "choice_id", "source"],
                            },
                        },
                        "disable_intimate_content": {
                            "type": "boolean",
                            "default": False,
                        },
                    },
                    "required": ["age", "sex", "evidence"],
                },
            ),
            # diagnosis
            Tool(
                name="diagnosis",
                description="Method to diagnose the patient based on the initial observations and symptoms",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "age": {"type": "integer", "description": "Patient's age"},
                        "sex": {
                            "type": "string",
                            "description": "Patient's biological sex",
                        },
                        "evidence": {
                            "type": "array",
                            "description": "List of evidence objects",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "string"},
                                    "choice_id": {
                                        "type": "string",
                                        "enum": ["present", "absent", "unknown"],
                                    },
                                },
                                "required": ["id", "choice_id"],
                            },
                        },
                        "disable_intimate_content": {
                            "type": "boolean",
                            "default": False,
                        },
                    },
                    "required": ["age", "sex", "evidence"],
                },
            ),
            # search_concepts
            Tool(
                name="search_concepts",
                description="Search known medical concepts from Infermedica knowledge library",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "phrase": {
                            "type": "string",
                            "description": "Medical phrase to search for",
                        },
                        "age": {"type": "integer", "description": "Patient's age"},
                        "sex": {
                            "type": "string",
                            "description": "Patient's biological sex (male/female)",
                        },
                    },
                    "required": ["phrase", "age", "sex"],
                },
            ),
            # generate_interview_id
            Tool(
                name="generate_interview_id",
                description="Generate random secure Interview ID for the session",
                inputSchema={"type": "object", "properties": {}},
            ),
            # check_health
            Tool(
                name="check_health",
                description="Check health of backend api service",
                inputSchema={"type": "object", "properties": {}},
            ),
            # book_appointment
            Tool(
                name="book_appointment",
                description="Books an appointment with the GP",
                inputSchema={"type": "object", "properties": {}},
            ),
            # get_general_practice_information
            Tool(
                name="get_general_practice_information",
                description="Retrieves GP information including opening times and location",
                inputSchema={"type": "object", "properties": {}},
            ),
            #  check_time
            Tool(
                name="check_time",
                description="Checks current time and returns formatted time",
                inputSchema={"type": "object", "properties": {}},
            ),
            # store_evidence
            Tool(
                name="store_evidence",
                description="Stores patient symptoms/evidence in the global evidence list",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "evidence": {
                            "type": "object",
                            "description": "Evidence object with id, choice_id (present/absent/unknown), and source",
                        }
                    },
                    "required": ["evidence"],
                },
            ),
            # clear_evidence_cache
            Tool(
                name="clear_evidence_cache",
                description="Clears the evidence list and evidence set stored values",
                inputSchema={"type": "object", "properties": {}},
            ),
            # get_evidence_list
            Tool(
                name="get_evidence_list",
                description="Returns the current evidence list",
                inputSchema={"type": "object", "properties": {}},
            ),
            # get_patient_data
            Tool(
                name="get_patient_data",
                description="This method retrives the patient data from the database backend service",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "patient_id": {
                            "type": "integer",
                            "description": "Unique id to retrive the information about that patient",
                        }
                    },
                    "required": ["patient_id"],
                },
            ),
            # start_call_session
            Tool(
                name="start_call_session",
                description="Start a new medical call session for a patient",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "patient_id": {
                            "type": "integer",
                            "description": "The ID of the patient initiating the call session",
                        }
                    },
                    "required": ["patient_id"],
                },
            ),
            # end_call_session
            Tool(
                name="end_call_session",
                description="End an active call session",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "call_id": {
                            "type": "integer",
                            "description": "The ID of the call session to terminate",
                        }
                    },
                    "required": ["call_id"],
                },
            ),
            # create_interview
            Tool(
                name="create_interview",
                description="Create a new diagnosis interview record for a patient",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "patient_id": {
                            "type": "integer",
                            "description": "The ID of the patient receiving the diagnosis",
                        },
                        "title": {
                            "type": "string",
                            "description": "Brief title summarizing the diagnosis",
                        },
                        "description": {
                            "type": "string",
                            "description": "Detailed description of the diagnosis",
                        },
                        "report": {
                            "type": "string",
                            "description": "Complete diagnostic report with findings and recommendations",
                        },
                    },
                    "required": ["patient_id", "title", "description", "report"],
                },
            ),
            # update_interview
            Tool(
                name="update_interview",
                description="Update an existing diagnosis record",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "diagnosis_id": {
                            "type": "integer",
                            "description": "The ID of the diagnosis to update",
                        },
                        "title": {
                            "type": "string",
                            "description": "Updated diagnosis title",
                        },
                        "description": {
                            "type": "string",
                            "description": "Updated diagnosis description",
                        },
                        "report": {
                            "type": "string",
                            "description": "Updated diagnostic report",
                        },
                    },
                    "required": ["diagnosis_id", "title", "description", "report"],
                },
            ),
            # create_interview_session
            Tool(
                name="create_interview_session",
                description="Create a diagnosis session linking a call session to a diagnosis",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "call_id": {
                            "type": "integer",
                            "description": "The ID of the call session",
                        },
                        "diagnosis_id": {
                            "type": "integer",
                            "description": "The ID of the diagnosis to link",
                        },
                    },
                    "required": ["call_id", "diagnosis_id"],
                },
            ),
            # create_chat
            Tool(
                name="create_chat",
                description="Create a new chat message in the call session history",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "call_id": {
                            "type": "integer",
                            "description": "The ID of the call session",
                        },
                        "role": {
                            "type": "string",
                            "description": "The role of the message sender (e.g., 'patient', 'doctor', 'system')",
                        },
                        "content": {
                            "type": "string",
                            "description": "The text content of the chat message",
                        },
                    },
                    "required": ["call_id", "role", "content"],
                },
            ),
        ]
        print(f"DEBUG: Returning {len(tools)} tools")
        return tools
    except Exception as e:
        print(f"ERROR in list_tools: {e}")
        return []


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> List[TextContent]:
    """Handle tool calls"""

    try:
        print(f"DEBUG: Calling tool {name} with arguments: {arguments}")

        if name == "parse_text":
            result = await parse_text(
                arguments["text"], arguments["age"], arguments["sex"]
            )
            return [TextContent(type="text", text=result)]

        elif name == "suggest":
            result = await suggest(
                arguments["age"],
                arguments["sex"],
                arguments["evidence"],
                arguments.get("disable_intimate_content", False),
            )
            return [TextContent(type="text", text=result)]

        elif name == "check_health":
            result = await check_health()
            return [TextContent(type="text", text=result)]

        elif name == "diagnosis":
            result = await diagnosis(
                arguments["age"],
                arguments["sex"],
                arguments["evidence"],
                arguments.get("disable_intimate_content", False),
            )
            return [TextContent(type="text", text=result)]

        elif name == "search_concepts":
            result = await search_concepts(
                arguments["phrase"], arguments["age"], arguments["sex"]
            )
            return [TextContent(type="text", text=result)]

        elif name == "generate_interview_id":
            result = await generate_interview_id()
            return [TextContent(type="text", text=result)]

        elif name == "book_appointment":
            result = await book_appointment()
            return [TextContent(type="text", text=result)]

        elif name == "get_general_practice_information":
            result = await get_general_practice_information()
            return [TextContent(type="text", text=result)]

        elif name == "check_time":
            result = await check_time()
            return [TextContent(type="text", text=result)]

        elif name == "store_evidence":
            result = await store_evidence(arguments["evidence"])
            return [TextContent(type="text", text=result)]

        elif name == "clear_evidence_cache":
            result = await clear_evidence_cache()
            return [TextContent(type="text", text=result)]

        elif name == "get_evidence_list":
            result = await get_evidence_list()
            return [TextContent(type="text", text=result)]

        elif name == "get_patient_data":
            result = await get_patient_data(arguments["patient_id"])
            return [TextContent(type="text", text=result)]

        elif name == "start_call_session":
            result = await start_call_session(arguments["patient_id"])
            return [TextContent(type="text", text=result)]

        elif name == "end_call_session":
            result = await end_call_session(arguments["call_id"])
            return [TextContent(type="text", text=result)]

        elif name == "create_interview":
            result = await create_interview(
                arguments["patient_id"],
                arguments["title"],
                arguments["description"],
                arguments["report"],
            )
            return [TextContent(type="text", text=result)]

        elif name == "update_interview":
            result = await update_interview(
                arguments["diagnosis_id"],
                arguments["title"],
                arguments["description"],
                arguments["report"],
            )
            return [TextContent(type="text", text=result)]

        elif name == "create_interview_session":
            result = await create_interview_session(
                arguments["call_id"], arguments["diagnosis_id"]
            )
            return [TextContent(type="text", text=result)]

        elif name == "create_chat":
            result = await create_chat(
                arguments["call_id"], arguments["role"], arguments["content"]
            )
            return [TextContent(type="text", text=result)]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        print(f"ERROR in call_tool: {e}")
        return [TextContent(type="text", text=f"Error executing tool {name}: {str(e)}")]


async def parse_text(text: str, age: int, sex: str) -> str:
    """NLP service for parsing natural text from patients to identify medical concepts."""
    headers = {
        "App-Id": app_id,
        "App-Key": app_key,
        "Interview-Id": interview_id,
        "Content-Type": "application/json",
    }

    payload = {
        "text": text,
        "age": {"value": age},
        "sex": sex.lower(),
        "include_tokens": True,
    }

    try:
        response = requests.post(
            f"{base_url}/parse",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        result = response.json()
        return json.dumps(result, indent=2)
    except requests.RequestException as e:
        return f"Error parsing text: {str(e)}"


async def suggest(
    age: int,
    sex: str,
    evidence: List[Dict[str, str]],
    disable_intimate_content: bool = False,
) -> str:
    """Method to refine the initial observation (symptoms, and conditions)."""
    headers = {
        "App-Id": app_id,
        "App-Key": app_key,
        "Interview-Id": interview_id,
        "Content-Type": "application/json",
    }

    payload = {
        "age": {"value": age},
        "sex": sex.lower(),
        "evidence": evidence,
        "suggest_method": "symptoms",
        "extras": {
            "disable_intimate_content": disable_intimate_content,
        },
    }

    try:
        response = requests.post(
            f"{base_url}/suggest?max_results=6",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        result = response.json()
        return json.dumps(result, indent=2)
    except requests.RequestException as e:
        return f"Error getting suggestions: {str(e)}"


async def diagnosis(
    age: int,
    sex: str,
    evidence: List[Dict[str, str]],
    disable_intimate_content: bool = False,
) -> str:
    """Method to diagnose the patient based on the initial observations and symptoms."""
    headers = {
        "App-Id": app_id,
        "App-Key": app_key,
        "Interview-Id": interview_id,
        "Content-Type": "application/json",
    }

    payload = {
        "age": {"value": age},
        "sex": sex.lower(),
        "evidence": evidence,
        "extras": {
            "disable_groups": False,
            "disable_intimate_content": disable_intimate_content,
        },
    }

    try:
        response = requests.post(
            f"{base_url}/diagnosis",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        result = response.json()
        return json.dumps(result, indent=2)
    except requests.RequestException as e:
        return f"Error getting diagnosis: {str(e)}"


async def search_concepts(phrase: str, age: int, sex: str) -> str:
    """Search known medical concepts from Infermedica knowledge library."""
    params = {
        "phrase": phrase,
        "age.value": age,
        "sex": sex.lower(),
    }

    headers = {
        "App-Id": app_id,
        "App-Key": app_key,
        "Interview-Id": interview_id,
    }

    try:
        response = requests.get(
            f"{base_url}/search",
            params=params,
            headers=headers,
        )
        response.raise_for_status()

        if response.status_code == 200:
            result = response.json()
            return json.dumps(result, indent=2)
        else:
            return f"Search failed with status code: {response.status_code}"
    except requests.RequestException as e:
        return f"Error searching concepts: {str(e)}"


async def generate_interview_id() -> str:
    """Generate random secure Interview ID for the session."""
    global interview_id
    interview_id = str(uuid4())
    return f"Generated interview ID: {interview_id}"


async def book_appointment() -> str:
    """Books an appointment with the GP."""
    result = {
        "status": "success",
        "message": "Appointment booked successfully",
        "appointment_id": str(uuid4()),
        "scheduled_time": "Next available slot will be confirmed via phone",
    }
    return json.dumps(result, indent=2)


async def get_general_practice_information() -> str:
    """Retrieves GP information including opening times and location."""
    result = {
        "name": "Briton Street Surgery",
        "opening_times": {
            "monday": {"open": "9am", "close": "5pm"},
            "tuesday": {"open": "9am", "close": "5pm"},
            "wednesday": {"open": "9am", "close": "5pm"},
            "thursday": {"open": "9am", "close": "5pm"},
            "friday": {"open": "9am", "close": "5pm"},
            "saturday": {"open": "10am", "close": "5pm"},
            "sunday": {"open": "10am", "close": "3pm"},
        },
        "location": "LE1 9BH, Briton Street Surgery, Leicester",
    }
    return json.dumps(result, indent=2)


async def check_time() -> str:
    """Checks current time and returns formatted time."""
    current_time = datetime.now()
    now = current_time.strftime("%I:%M:%S %p")
    return now


async def store_evidence(evidence: Dict[str, str]) -> str:
    """Stores patient symptoms/evidence in the global evidence list."""
    if evidence["id"] not in evidence_set:
        evidence_set.add(evidence["id"])
        evidence_list.append(evidence)
        return f"Evidence stored: {json.dumps(evidence, indent=2)}"
    else:
        return f"Evidence already exists: {evidence['id']}"


async def clear_evidence_cache() -> str:
    """Clears the evidence list and evidence set stored values."""
    global evidence_list, evidence_set
    evidence_list.clear()
    evidence_set.clear()
    return "Evidence cache cleared successfully"


async def get_evidence_list() -> str:
    """Returns the current evidence list."""
    return json.dumps(evidence_list, indent=2)


async def check_health() -> str:
    """This method health of api service."""
    global patient_data_cache

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    try:
        response = requests.get(
            f"{backend_base_url}/health",
            headers=headers,
        )
        response.raise_for_status()

        print(f"Response: {response.json()}")
        print(f"Response status code: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            patient_data_cache = result
            return json.dumps(result, indent=2)
        else:
            return f"Request failed with status code: {response.status_code}"
    except requests.RequestException as e:
        print(f"Response: {response.json()}")
        print(f"Response status code: {response.status_code}")
        print(f"Error - Request exception: {e}")
        return f"Error checking health: {str(e)}"


async def get_patient_data(patient_id: int) -> str:
    """This method retrives the patient data from the database backend service."""
    global patient_data_cache

    headers = {
        "Accept": "application/json",
        "Authorization": access_token,
    }

    try:
        response = requests.get(
            f"{backend_base_url}/{backend_api_router}/patients/{patient_id}",
            params={},
            headers=headers,
        )
        print(f"\nURL: {backend_base_url}/{backend_api_router}/patients/{patient_id}\n")

        response.raise_for_status()

        if response.status_code == 200:
            result = response.json()
            patient_data_cache = result
            return json.dumps(result, indent=2)
        else:
            return f"Request failed with status code: {response.status_code}"
    except requests.RequestException as e:
        return f"Error fetching patient data: {str(e)}"


async def start_call_session(patient_id: int) -> str:
    """Start a new medical call session for a patient."""
    headers = {
        "Accept": "application/json",
        "Authorization": access_token,
    }

    payload = {"patient_id": patient_id}

    try:
        url = f"{backend_base_url}/{backend_api_router}/call-sessions/"
        print(f"DEBUG: Starting call session - URL: {url}")
        print(f"DEBUG: Payload: {payload}")
        print(f"DEBUG: Headers: {headers}")

        response = requests.post(url, headers=headers, json=payload)

        print(f"DEBUG: Response status: {response.status_code}")
        print(f"DEBUG: Response headers: {dict(response.headers)}")
        print(f"DEBUG: Response content: '{response.text}'")

        response.raise_for_status()

        if not response.text.strip():
            return json.dumps({"error": "Empty response from server"})

        result = response.json()
        return json.dumps(result, indent=2)

    except requests.RequestException as e:
        print(f"DEBUG: Request exception: {e}")
        return json.dumps({"error": f"Request failed: {str(e)}"})
    except json.JSONDecodeError as e:
        print(f"DEBUG: JSON decode error: {e}")
        return json.dumps(
            {
                "error": f"Invalid JSON response: {str(e)}",
                "raw_response": response.text[:200],
            }
        )


async def end_call_session(call_id: int) -> str:
    """End an active call session."""
    headers = {
        "Accept": "application/json",
        "Authorization": access_token,
    }

    try:
        response = requests.post(
            f"{backend_base_url}/{backend_api_router}/call-sessions/{call_id}/end",
            headers=headers,
            json={},
        )
        response.raise_for_status()
        result = response.json()
        return json.dumps(result, indent=2)
    except requests.RequestException as e:
        return f"Error ending call session: {str(e)}"


async def create_interview(
    patient_id: int,
    title: str,
    description: str,
    report: str,
) -> str:
    """Create a new diagnosis interview record for a patient."""
    headers = {
        "Accept": "application/json",
        "Authorization": access_token,
    }

    payload = {
        "patient_id": patient_id,
        "title": title,
        "description": description,
        "report": report,
    }

    try:
        response = requests.post(
            f"{backend_base_url}/{backend_api_router}/diagnoses/",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        result = response.json()
        return json.dumps(result, indent=2)
    except requests.RequestException as e:
        return f"Error creating diagnosis interview: {str(e)}"


async def update_interview(
    diagnosis_id: int,
    title: str,
    description: str,
    report: str,
) -> str:
    """Update an existing diagnosis record."""
    headers = {
        "Accept": "application/json",
        "Authorization": access_token,
    }

    payload = {
        "title": title,
        "description": description,
        "report": report,
    }

    try:
        response = requests.put(
            f"{backend_base_url}/{backend_api_router}/diagnoses/{diagnosis_id}/",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        result = response.json()
        return json.dumps(result, indent=2)
    except requests.RequestException as e:
        return f"Error updating diagnosis interview: {str(e)}"


async def create_interview_session(call_id: int, diagnosis_id: int) -> str:
    """Create a diagnosis session linking a call session to a diagnosis."""
    headers = {
        "Accept": "application/json",
        "Authorization": access_token,
    }

    payload = {
        "call_id": call_id,
        "diagnosis_id": diagnosis_id,
    }

    try:
        response = requests.post(
            f"{backend_base_url}/{backend_api_router}/diagnosis-sessions/",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        result = response.json()
        return json.dumps(result, indent=2)
    except requests.RequestException as e:
        return f"Error creating diagnosis session: {str(e)}"


async def create_chat(call_id: int, role: str, content: str) -> str:
    """Create a new chat message in the call session history."""
    headers = {
        "Accept": "application/json",
        "Authorization": access_token,
    }

    payload = {
        "call_id": call_id,
        "speaker": role,
        "message_text": content,
    }

    try:
        response = requests.post(
            f"{backend_base_url}/{backend_api_router}/chat-history/",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        result = response.json()
        return json.dumps(result, indent=2)
    except requests.RequestException as e:
        return f"Error creating chat: {str(e)}"


async def main():
    """Run the server using stdio transport"""
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


if __name__ == "__main__":
    print("Starting GP Voice Agent MCP server...")
    asyncio.run(main())
