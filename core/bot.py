import asyncio
import os
import sys
import aiohttp
from typing import Dict, Any, List, Optional, Set
import threading
from datetime import datetime
import json

from dotenv import load_dotenv
from loguru import logger

# from runner import configure

from pipecat_flows import (
    FlowManager,
    FlowResult,
    NodeConfig,
    ContextStrategyConfig,
    ContextStrategy,
)
from pipecat_flows.types import ActionConfig, FlowsFunctionSchema

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.services.openai.llm import OpenAILLMService
from pipecat.services.elevenlabs.tts import ElevenLabsTTSService
from pipecat.services.openai.stt import OpenAISTTService
from pipecat.transports.services.daily import DailyParams, DailyTransport
from pipecat.utils.text.markdown_text_filter import MarkdownTextFilter
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.services.openai.llm import OpenAILLMService
from pipecat.services.elevenlabs.tts import ElevenLabsTTSService
from pipecat.services.openai.stt import OpenAISTTService
from pipecat.transports.services.daily import DailyParams, DailyTransport
from pipecat.utils.text.markdown_text_filter import MarkdownTextFilter
from pipecat.frames.frames import EndFrame
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from pipecat.services.openai.tts import OpenAITTSService

from pipecat_flows import FlowManager

from core.prompt_templates.initial_node_template import (
    ROLE_MESSAGE,
    INITIAL_TASK_MESSAGE,
)
from core.prompt_templates.diagnosis_node_template import (
    DIAGNOSIS_TASK_MESSAGE_V02,
    DIAGNOSIS_TASK_MESSAGE_V03,
)
from core.prompt_templates.suggest_node_template import SUGGEST_TASK_MESSAGE

from core.mcp_client import mcp_client
from core.simple_sentence_filter import create_simple_sentence_filter


load_dotenv(override=True)

# Environment credentials
openai_api_key = os.environ.get("OPENAI_API_KEY")
llm_model = os.environ.get("LLM_MODEL")
tts_model = os.environ.get("TTS_MODEL")
stt_model = os.environ.get("STT_MODEL")
elevenlabs_api_key = os.environ.get("ELEVENLABS_API_KEY")
elevenlabs_voice_id = os.environ.get("ELEVENLABS_VOICE_ID")

logger.remove(0)
logger.add(sys.stderr, level="DEBUG")

# Global MCP client instance - Single source of truth for state
# mcp_client = MCPClient()


# Global variables for evidence tracking
evidence_list: List[Dict[str, str]] = []
evidence_set: set = set()

# === CUSTOM FUNCTIONS (Not MCP Tools) ===


async def store_evidence_to_state(actions: dict, flow_manager: FlowManager):
    """
    Retrieve evidence list from MCP server and store in FlowManager state for conversation context.
    """
    try:
        # Get current evidence from MCP server (single source of truth)
        evidence_result = await mcp_client.call_tool("get_evidence_list", {})

        if evidence_result:
            import json

            evidence_list = json.loads(evidence_result)
            flow_manager.state["evidence_list"] = evidence_list

            logger.info(
                f"Evidence list retrieved from MCP and stored in flow state: {len(evidence_list)} items"
            )
            return {
                "status": "success",
                "message": "Evidence retrieved from MCP server and stored in conversation state.",
                "evidence_list": evidence_list,
            }
        else:
            logger.warning("No evidence returned from MCP server")
            flow_manager.state["evidence_list"] = []
            return {
                "status": "warning",
                "message": "No evidence found on MCP server",
                "evidence_list": [],
            }

    except Exception as e:
        logger.error(f"Failed to retrieve evidence from MCP server: {e}")
        flow_manager.state["evidence_list"] = []
        return {
            "status": "error",
            "message": f"Failed to get evidence from MCP: {str(e)}",
            "evidence_list": [],
        }


# Enhanced function handlers that use MCP


async def get_patient_data_mcp(action: Dict[str, Any], flow_manager: FlowManager):
    """
    Enhanced patient data retrieval using MCP
    """
    try:
        # Call MCP server tool instead of local implementation
        result = await mcp_client.call_tool(
            "get_patient_data",
            # the patient_id value will be dynamic when the mobile app is developed and passed through an api endpoint
            {"patient_id": 3},
        )

        if result:
            import json

            patient_data = json.loads(result)
            flow_manager.state["patient_data"] = patient_data
            logger.info("Patient data retrieved via MCP")
            return patient_data
        else:
            # Fallback to local implementation
            return await get_patient_data_local(action, flow_manager)

    except Exception as e:
        logger.error(f"MCP patient data retrieval failed: {e}")
        # Fallback to local implementation
        return await get_patient_data_local(action, flow_manager)


async def get_patient_data_local(action: Dict[str, Any], flow_manager: FlowManager):
    """
    Local fallback for patient data retrieval
    """
    await asyncio.sleep(0.2)

    patient_data = {
        "fullname": "Shafiq Shafi",
        "dob": "1975-07-02",
        "age": 46,
        "gender": "Male",
        "symptoms": "",
        "conditions": "",
        "phone": "9860867453",
        "address": "Bede Hall, Leicester, LE2 7EQ",
        "emergency_contact_name": "Bob Miller",
        "emergency_contact_phone": "9867897645",
        "patient_id": 3,
        "user_id": 5,
        "created_at": "2025-07-15T18:16:45",
        "updated_at": "",
    }

    flow_manager.state["patient_data"] = patient_data
    return patient_data


async def process_text_mcp(
    actions: Optional[Dict[str, Any]] = None,
    flow_manager: Optional[FlowManager] = None,
):
    """
    Enhanced text processing using MCP parse_text tool
    """
    try:
        patient_data = flow_manager.state.get("patient_data")
        context_message = flow_manager.get_current_context()

        # Extract user message from context
        initial_text = ""
        for message in context_message:
            if message.get("role") == "user":
                initial_text += message.get("content")

        flow_manager.state["initial_text"] = initial_text
        logger.info(f"Processing text via MCP: {initial_text[:100]}...")

        # Call MCP parse_text tool
        mcp_args = {
            "text": initial_text,
            "age": patient_data["age"],
            "sex": patient_data["gender"],
        }

        result = await mcp_client.call_tool("parse_text", mcp_args)

        if result:
            import json

            parsed_symptoms = json.loads(result)

            # Store evidence using MCP
            for symptom in parsed_symptoms.get("mentions", []):
                evidence = {
                    "id": symptom["id"],
                    "choice_id": symptom["choice_id"],
                    "source": "initial",
                }
                await store_evidence_mcp(evidence)

            flow_manager.state["parsed_symptoms"] = parsed_symptoms
            logger.info("Text processed via MCP successfully")
            return parsed_symptoms
        else:
            raise Exception("No result from MCP parse_text")

    except Exception as e:
        logger.error(f"MCP text processing failed: {e}")
        # Could implement local fallback here
        raise


async def suggest_symptoms_mcp(
    actions: Optional[Dict[str, Any]] = None,
    flow_manager: Optional[FlowManager] = None,
):
    """
    Enhanced symptom suggestion using MCP
    """
    try:
        patient_data = flow_manager.state.get("patient_data")
        parsed_symptoms = flow_manager.state.get("parsed_symptoms")

        if parsed_symptoms is None:
            raise Exception(
                "No parsed symptoms found. Need to call process_text first."
            )

        # Prepare evidence for MCP call
        evidence = []
        for symptom in parsed_symptoms["mentions"]:
            evidence.append(
                {
                    "id": symptom["id"],
                    "choice_id": symptom["choice_id"],
                    "source": "initial",
                }
            )

        flow_manager.state["initial_evidence"] = evidence

        # Call MCP suggest tool
        mcp_args = {
            "age": patient_data["age"],
            "sex": patient_data["gender"],
            "evidence": evidence,
            "disable_intimate_content": False,
        }

        result = await mcp_client.call_tool("suggest", mcp_args)

        if result:
            import json

            suggested_symptoms = json.loads(result)
            flow_manager.state["suggested_symptoms"] = suggested_symptoms
            logger.info("Symptoms suggested via MCP successfully")
            return suggested_symptoms
        else:
            raise Exception("No result from MCP suggest")

    except Exception as e:
        logger.error(f"MCP symptom suggestion failed: {e}")
        raise


async def store_evidence_mcp(evidence: Dict[str, str]):
    """
    Store evidence using MCP server
    """
    try:
        # Call MCP store_evidence tool
        result = await mcp_client.call_tool("store_evidence", {"evidence": evidence})

        # Also maintain local evidence list for compatibility
        if evidence["id"] not in evidence_set:
            evidence_set.add(evidence["id"])
            evidence_list.append(evidence)
            logger.info(f"Evidence stored via MCP: {evidence['id']}")

        return {
            "status": "success",
            "message": f"Symptom {evidence['id']} recorded as {evidence['choice_id']}",
        }

    except Exception as e:
        logger.error(f"MCP evidence storage failed: {e}")
        # Fallback to local storage
        return await store_evidence_local(evidence)


async def store_evidence_local(evidence: Dict[str, str]):
    """
    Local fallback for evidence storage
    """
    if evidence["id"] not in evidence_set:
        evidence_set.add(evidence["id"])
        evidence_list.append(evidence)
        logger.info(f"Evidence stored locally: {evidence['id']}")

    return {
        "status": "success",
        "message": f"Symptom {evidence['id']} recorded as {evidence['choice_id']}",
    }


async def run_diagnosis_mcp(args: dict, flow_manager: FlowManager):
    """
    Enhanced diagnosis using MCP
    """
    try:
        patient_data = flow_manager.state.get("patient_data")

        # Get current evidence list from MCP
        evidence_result = await mcp_client.call_tool("get_evidence_list", {})

        if evidence_result:
            import json

            current_evidence = json.loads(evidence_result)
        else:
            current_evidence = evidence_list  # Fallback to local

        # Call MCP diagnosis tool
        mcp_args = {
            "age": patient_data["age"],
            "sex": patient_data["gender"],
            "evidence": current_evidence,
            "disable_intimate_content": False,
        }

        result = await mcp_client.call_tool("diagnosis", mcp_args)

        if result:
            import json

            diagnosis_response = json.loads(result)

            # Check if we should stop
            should_stop = diagnosis_response.get("should_stop", False)
            question = diagnosis_response.get("question")

            if should_stop or question is None:
                return {
                    "status": "complete",
                    "message": "Diagnosis interview complete",
                    "should_stop": True,
                    "final_response": diagnosis_response,
                }

            # Store in flow manager state
            flow_manager.state["last_diagnosis_response"] = diagnosis_response
            flow_manager.state["current_question"] = question
            flow_manager.state["question_type"] = question.get("type")

            return {
                "status": "success",
                "should_stop": False,
                "question": question,
                "question_type": question.get("type"),
                "question_text": question.get("text"),
                "items": question.get("items", []),
            }
        else:
            raise Exception("No result from MCP diagnosis")

    except Exception as e:
        logger.error(f"MCP diagnosis failed: {e}")
        return {
            "status": "error",
            "message": f"Diagnosis failed: {str(e)}",
            "should_stop": True,
        }


async def clear_evidence_cache_mcp(actions: dict, flow_manager: FlowManager):
    """
    Clear evidence cache using MCP
    """
    try:
        await mcp_client.call_tool("clear_evidence_cache", {})

        # Also clear local cache
        evidence_list.clear()
        evidence_set.clear()

        logger.info("Evidence cache cleared via MCP")

    except Exception as e:
        logger.error(f"MCP cache clear failed: {e}")
        # Fallback to local clear
        evidence_list.clear()
        evidence_set.clear()


async def check_time_mcp():
    """
    Enhanced time checking using MCP
    """
    try:
        result = await mcp_client.call_tool("check_time", {})
        return result
    except Exception as e:
        logger.error(f"MCP time check failed: {e}")
        # Fallback to local implementation
        from datetime import datetime

        current_time = datetime.now()
        return current_time.strftime("%I:%M:%S %p")


async def get_general_practice_information_mcp() -> dict:
    """
    Enhanced GP info retrieval using MCP
    """
    try:
        result = await mcp_client.call_tool("get_general_practice_information", {})
        if result:
            import json

            return json.loads(result)
    except Exception as e:
        logger.error(f"MCP GP info retrieval failed: {e}")

    # Fallback to local data
    return {
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


async def book_an_appointment_mcp() -> dict:
    """
    Enhanced appointment booking using MCP
    """
    try:
        result = await mcp_client.call_tool("book_appointment", {})
        if result:
            import json

            return json.loads(result)
    except Exception as e:
        logger.error(f"MCP appointment booking failed: {e}")

    # Fallback response
    return {
        "status": "success",
        "message": "Appointment booking request received",
        "note": "You will be contacted to confirm the appointment",
    }


async def start_call_session_mcp(args: dict, flow_manager: FlowManager):
    """
    Start call session with dynamic patient_id from real patient data
    """
    try:
        patient_data = flow_manager.state.get("patient_data")

        if not patient_data:
            logger.warning("No patient data available for call session")
            return {"status": "error", "message": "No patient data available"}

        # Use real patient_id from the API response
        patient_id = patient_data["patient_id"]  # This will be 3 based on your data

        mcp_args = {"patient_id": patient_id}

        logger.info(f"Starting call session for patient_id: {patient_id}")
        result = await mcp_client.call_tool("start_call_session", mcp_args)

        if result:
            response = json.loads(result)

            # ✅ Check if there's an error in the response
            if "error" in response:
                logger.error(f"Call session creation failed: {response['error']}")
                # Create fallback call session
                fallback_call_session = {
                    "status": "fallback",
                    "data": {
                        "patient_id": patient_id,
                        "call_id": 999,  # Fallback call_id
                        "start_time": datetime.now().isoformat(),
                        "end_time": None,
                    },
                }
                flow_manager.state["call_session"] = fallback_call_session
                flow_manager.state["call_id"] = 999
                return {"status": "fallback", "message": "Using fallback call session"}

    except Exception as e:
        logger.error(f"MCP start call session failed: {e}")
        return {"status": "error", "message": f"Start call session failed: {str(e)}"}


async def end_call_session_mcp(args: dict, flow_manager: FlowManager):
    """
    End call session with dynamic call_id from active session
    """
    try:
        call_session = flow_manager.state.get("call_session")

        if not call_session:
            logger.warning("No active call session to end")
            return {"status": "skipped", "message": "No active call session"}

        # Extract call_id from stored call session
        call_id = None
        if isinstance(call_session, dict) and "data" in call_session:
            call_id = call_session["data"].get("call_id")

        if not call_id:
            logger.warning("No call_id found in session data")
            return {"status": "error", "message": "No call_id available"}

        mcp_args = {"call_id": call_id}

        logger.info(f"Ending call session: call_id={call_id}")
        result = await mcp_client.call_tool("end_call_session", mcp_args)

        if result:
            response = json.loads(result)

            # Expected response: {"patient_id": 3, "start_time": "...", "end_time": "2025-07-18T20:36:40.425093", "call_id": 7, "created_at": "..."}
            flow_manager.state["ended_call_session"] = response

            logger.info(f"Call session {call_id} ended successfully")

            return {
                "status": "success",
                "message": f"Call session {call_id} ended successfully",
                "data": response,
            }
        else:
            raise Exception("No result from MCP end_call_session")

    except Exception as e:
        logger.error(f"MCP end call session failed: {e}")
        return {"status": "error", "message": f"End call session failed: {str(e)}"}


# async def start_call_session_mcp(args: dict, flow_manager: FlowManager):
#     """
#     Start call session with dynamic patient_id from real patient data
#     """
#     try:
#         patient_data = flow_manager.state.get("patient_data")

#         if not patient_data:
#             logger.warning("No patient data available for call session")
#             return {"status": "error", "message": "No patient data available"}

#         # Use real patient_id from the API response
#         patient_id = patient_data.get("patient_id", 3)  # Default fallback to 3

#         mcp_args = {"patient_id": patient_id}

#         logger.info(f"Starting call session for patient_id: {patient_id}")
#         result = await mcp_client.call_tool("start_call_session", mcp_args)

#         if result:
#             response = json.loads(result)

#             # Check if there's an error in the response
#             if "error" in response:
#                 logger.error(f"Call session creation failed: {response['error']}")
#                 # Store a fallback call session with a generated ID
#                 fallback_call_session = {
#                     "status": "fallback",
#                     "message": "Call session created with fallback ID",
#                     "data": {
#                         "patient_id": patient_id,
#                         "call_id": 999,  # Fallback call_id
#                         "start_time": datetime.now().isoformat(),
#                         "created_at": datetime.now().isoformat(),
#                         "end_time": None,
#                     },
#                 }
#                 flow_manager.state["call_session"] = fallback_call_session
#                 flow_manager.state["call_id"] = 999

#                 return {
#                     "status": "fallback",
#                     "message": f"Call session fallback created for patient {patient_id}",
#                     "data": fallback_call_session["data"],
#                 }

#             # Store the complete call session response
#             # Expected response: {"patient_id": 3, "start_time": "2025-07-18T20:36:56.798269", "end_time": null, "call_id": 8, "created_at": "2025-07-18T20:36:56"}
#             call_session_data = {
#                 "status": "success",
#                 "message": "Call session started",
#                 "data": response,
#             }
#             flow_manager.state["call_session"] = call_session_data
#             flow_manager.state["call_id"] = response.get("call_id")

#             logger.info(
#                 f"Call session started: call_id={response.get('call_id')}, patient_id={patient_id}"
#             )

#             return {
#                 "status": "success",
#                 "message": f"Call session {response.get('call_id')} started for patient {patient_id}",
#                 "data": response,
#             }
#         else:
#             raise Exception("No result from MCP start_call_session")

#     except Exception as e:
#         logger.error(f"MCP start call session failed: {e}")

#         # Create fallback call session
#         patient_data = flow_manager.state.get("patient_data", {})
#         patient_id = patient_data.get("patient_id", 3)

#         fallback_call_session = {
#             "status": "fallback",
#             "message": "Call session created with fallback due to error",
#             "data": {
#                 "patient_id": patient_id,
#                 "call_id": 999,  # Fallback call_id
#                 "start_time": datetime.now().isoformat(),
#                 "created_at": datetime.now().isoformat(),
#                 "end_time": None,
#             },
#         }
#         flow_manager.state["call_session"] = fallback_call_session
#         flow_manager.state["call_id"] = 999

#         return {
#             "status": "fallback",
#             "message": f"Call session fallback created due to error: {str(e)}",
#         }


# async def end_call_session_mcp(args: dict, flow_manager: FlowManager):
#     """
#     End call session with dynamic call_id from active session
#     """
#     try:
#         call_session = flow_manager.state.get("call_session")

#         if not call_session:
#             logger.warning("No active call session to end")
#             return {"status": "skipped", "message": "No active call session"}

#         # Extract call_id from stored call session with multiple strategies
#         call_id = None

#         # Strategy 1: Extract from call_session data
#         if isinstance(call_session, dict) and "data" in call_session:
#             call_id = call_session["data"].get("call_id")

#         # Strategy 2: Try to get from flow state directly
#         if not call_id:
#             call_id = flow_manager.state.get("call_id")

#         # Strategy 3: Handle missing call_id
#         if not call_id:
#             logger.warning("No call_id found in session data")
#             return {"status": "error", "message": "No call_id available"}

#         # If it's a fallback call session, just mark as ended locally
#         if call_session.get("status") == "fallback":
#             logger.info(f"Ending fallback call session: call_id={call_id}")
#             flow_manager.state["ended_call_session"] = {
#                 "patient_id": call_session["data"]["patient_id"],
#                 "call_id": call_id,
#                 "start_time": call_session["data"]["start_time"],
#                 "end_time": datetime.now().isoformat(),
#                 "created_at": call_session["data"]["created_at"],
#             }
#             return {
#                 "status": "success",
#                 "message": f"Fallback call session {call_id} ended successfully",
#                 "data": flow_manager.state["ended_call_session"],
#             }

#         # For real call sessions, call the MCP API
#         mcp_args = {"call_id": call_id}

#         logger.info(f"Ending call session: call_id={call_id}")
#         result = await mcp_client.call_tool("end_call_session", mcp_args)

#         if result:
#             response = json.loads(result)

#             # Expected response: {"patient_id": 3, "start_time": "...", "end_time": "2025-07-18T20:36:40.425093", "call_id": 7, "created_at": "..."}
#             flow_manager.state["ended_call_session"] = response

#             logger.info(f"Call session {call_id} ended successfully")

#             return {
#                 "status": "success",
#                 "message": f"Call session {call_id} ended successfully",
#                 "data": response,
#             }
#         else:
#             raise Exception("No result from MCP end_call_session")

#     except Exception as e:
#         logger.error(f"MCP end call session failed: {e}")

#         # Fallback: mark session as ended locally
#         call_session = flow_manager.state.get("call_session", {})
#         call_id = flow_manager.state.get("call_id", 999)

#         fallback_end_session = {
#             "patient_id": call_session.get("data", {}).get("patient_id", 3),
#             "call_id": call_id,
#             "start_time": call_session.get("data", {}).get(
#                 "start_time", datetime.now().isoformat()
#             ),
#             "end_time": datetime.now().isoformat(),
#             "created_at": call_session.get("data", {}).get(
#                 "created_at", datetime.now().isoformat()
#             ),
#         }

#         flow_manager.state["ended_call_session"] = fallback_end_session

#         return {
#             "status": "fallback",
#             "message": f"Call session {call_id} ended with fallback due to error: {str(e)}",
#             "data": fallback_end_session,
#         }


async def create_interview_mcp(actions: dict, flow_manager: FlowManager):
    """
    Create a new diagnosis interview record with dynamic conversation data
    """
    try:
        patient_data = flow_manager.state.get("patient_data")

        if not patient_data:
            logger.warning("No patient data available for interview creation")
            return {"status": "skipped", "message": "No patient data available"}

        # Get conversation context to extract initial symptoms/complaints
        context_messages = flow_manager.get_current_context()

        # Extract the user's initial complaint from conversation
        user_messages = [msg for msg in context_messages if msg.get("role") == "user"]
        initial_complaint = ""
        symptoms_mentioned = []

        if user_messages:
            # Get the most recent user message that triggered the transition
            for msg in reversed(user_messages):
                content = msg.get("content", "").lower()
                if any(
                    keyword in content
                    for keyword in [
                        "feel",
                        "pain",
                        "hurt",
                        "sick",
                        "unwell",
                        "headache",
                        "fever",
                        "cough",
                    ]
                ):
                    initial_complaint = msg.get("content", "")
                    break

        # Extract symptoms from conversation
        for msg in user_messages:
            content = msg.get("content", "").lower()
            symptom_keywords = [
                "headache",
                "fever",
                "pain",
                "cough",
                "tired",
                "nausea",
                "dizzy",
                "ache",
            ]
            for keyword in symptom_keywords:
                if keyword in content and keyword not in symptoms_mentioned:
                    symptoms_mentioned.append(keyword)

        # Dynamic title based on patient and symptoms
        current_time = datetime.now()
        if symptoms_mentioned:
            primary_symptom = symptoms_mentioned[0].title()
            title = (
                f"{primary_symptom} diagnosis interview - {patient_data['fullname']}"
            )
        else:
            title = f"Medical consultation - {patient_data['fullname']}"

        # Dynamic description based on initial complaint
        if initial_complaint and symptoms_mentioned:
            description = f"Patient initiated this diagnosis interview by addressing {', '.join(symptoms_mentioned)} as initial symptoms"
        elif initial_complaint:
            description = f"Patient reported: {initial_complaint[:100]}..."
        else:
            description = "Patient-initiated medical assessment and symptom evaluation"

        # Dynamic report with comprehensive conversation data
        report_data = {
            "interview_metadata": {
                "patient_id": patient_data["patient_id"],
                "patient_name": patient_data["fullname"],
                "patient_age": patient_data["age"],
                "patient_gender": patient_data["gender"],
                "session_start": current_time.isoformat(),
                "interview_type": "symptoms_intake",
            },
            "initial_assessment": {
                "chief_complaint": initial_complaint,
                "symptoms_mentioned": symptoms_mentioned,
                "conversation_turns": len(user_messages),
                "assessment_trigger": "Patient mentioned feeling unwell",
            },
            "conversation_context": {
                "recent_messages": (
                    user_messages[-3:] if len(user_messages) >= 3 else user_messages
                ),
                "total_interactions": len(user_messages),
            },
            "clinical_status": {
                "status": "interview_started",
                "evidence_collected": 0,
                "next_phase": "symptom_collection",
            },
        }

        # Convert report to JSON string as expected by API
        report = json.dumps(report_data, indent=2)

        # Call MCP create_interview tool with real patient_id
        mcp_args = {
            "patient_id": patient_data[
                "patient_id"
            ],  # This will be 3 based on your data
            "title": title,
            "description": description,
            "report": report,
        }

        logger.info(f"Creating interview: {title}")
        result = await mcp_client.call_tool("create_interview", mcp_args)

        if result:
            response = json.loads(result)

            # Store the complete interview response in flow manager state
            # Expected response: {"patient_id": 3, "title": "...", "description": "...", "report": "...", "diagnosis_id": 3, "created_at": "2025-07-18T20:38:33"}
            flow_manager.state["current_interview"] = response
            flow_manager.state["diagnosis_id"] = response.get("diagnosis_id")

            logger.info(
                f"Interview created successfully with diagnosis_id: {response.get('diagnosis_id')}"
            )

            return {
                "status": "success",
                "message": f"Interview created for {symptoms_mentioned[0] if symptoms_mentioned else 'general consultation'}",
                "data": response,
            }
        else:
            raise Exception("No result from MCP create_interview")

    except Exception as e:
        logger.error(f"MCP create_interview failed: {e}")
        return {"status": "error", "message": f"create_interview failed: {str(e)}"}


async def update_interview_mcp(actions: dict, flow_manager: FlowManager):
    """
    Update interview with dynamic conversation progress and collected evidence
    """
    try:
        current_interview = flow_manager.state.get("current_interview")
        evidence_list = flow_manager.state.get("evidence_list", [])
        patient_data = flow_manager.state.get("patient_data")

        if not current_interview:
            logger.warning("No current interview to update")
            return {"status": "skipped", "message": "No interview to update"}

        diagnosis_id = current_interview.get("diagnosis_id")

        if not diagnosis_id:
            logger.warning("No diagnosis_id found for update")
            return {"status": "skipped", "message": "No diagnosis_id available"}

        # Get current conversation context for dynamic updates
        context_messages = flow_manager.get_current_context()
        user_messages = [msg for msg in context_messages if msg.get("role") == "user"]
        assistant_messages = [
            msg for msg in context_messages if msg.get("role") == "assistant"
        ]

        # Extract symptoms and progress dynamically
        symptoms_mentioned = []
        evidence_summary = []

        for msg in user_messages:
            content = msg.get("content", "").lower()
            symptom_keywords = [
                "headache",
                "fever",
                "pain",
                "cough",
                "tired",
                "nausea",
                "dizzy",
                "ache",
                "hurt",
            ]
            for keyword in symptom_keywords:
                if keyword in content and keyword not in symptoms_mentioned:
                    symptoms_mentioned.append(keyword)

        # Summarize evidence collected
        for evidence in evidence_list:
            if evidence.get("choice_id") == "present":
                evidence_summary.append(f"{evidence.get('id', 'unknown')}: confirmed")
            elif evidence.get("choice_id") == "absent":
                evidence_summary.append(f"{evidence.get('id', 'unknown')}: ruled out")

        # Dynamic title update with progress
        interaction_count = len(user_messages)
        if symptoms_mentioned:
            updated_title = f"{symptoms_mentioned[0].title()} diagnosis interview - {patient_data['fullname']} (Updated)"
        else:
            updated_title = (
                f"Medical consultation - {patient_data['fullname']} (Updated)"
            )

        # Dynamic description with current status
        if evidence_list:
            description = f"Interview progress: {len(evidence_list)} symptoms assessed. Primary concerns: {', '.join(symptoms_mentioned[:3]) if symptoms_mentioned else 'General health evaluation'}"
        else:
            description = f"Initial assessment completed. Patient mentioned: {symptoms_mentioned[0] if symptoms_mentioned else 'feeling unwell'}"

        # Comprehensive dynamic report update
        current_time = datetime.now()
        original_report = json.loads(current_interview.get("report", "{}"))

        updated_report_data = {
            **original_report,  # Preserve original data
            "interview_progress": {
                "last_updated": current_time.isoformat(),
                "total_interactions": interaction_count,
                "evidence_collected": len(evidence_list),
                "symptoms_discussed": symptoms_mentioned,
                "evidence_summary": evidence_summary,
            },
            "conversation_analysis": {
                "user_messages_count": len(user_messages),
                "assistant_responses_count": len(assistant_messages),
                "recent_conversation": (
                    user_messages[-2:] if len(user_messages) >= 2 else user_messages
                ),
                "conversation_duration_estimate": f"{interaction_count * 30} seconds",  # Rough estimate
            },
            "clinical_assessment": {
                "primary_symptoms": symptoms_mentioned[:3],  # Top 3 symptoms
                "evidence_details": evidence_list,
                "assessment_completeness": f"{min(100, (len(evidence_list) * 20))}%",  # Rough completion percentage
                "next_recommended_action": (
                    "Continue symptom assessment"
                    if len(evidence_list) < 5
                    else "Consider diagnosis phase"
                ),
            },
            "session_metadata": {
                "interview_phase": (
                    "evidence_collection" if evidence_list else "initial_consultation"
                ),
                "status": "in_progress",
                "last_update_timestamp": current_time.isoformat(),
            },
        }

        updated_report = json.dumps(updated_report_data, indent=2)

        # Call MCP update_interview tool with real diagnosis_id
        mcp_args = {
            "diagnosis_id": diagnosis_id,  # Real diagnosis_id from API
            "title": updated_title,
            "description": description,
            "report": updated_report,
        }

        logger.info(
            f"Updating interview {diagnosis_id} with {len(evidence_list)} evidence items"
        )
        result = await mcp_client.call_tool("update_interview", mcp_args)

        if result:
            response = json.loads(result)

            # Update the stored interview data
            flow_manager.state["current_interview"] = response

            logger.info(
                f"Interview {diagnosis_id} updated successfully with current progress"
            )

            return {
                "status": "success",
                "message": f"Interview updated with {len(evidence_list)} evidence items",
                "data": response,
            }
        else:
            raise Exception("No result from MCP update_interview")

    except Exception as e:
        logger.error(f"MCP update_interview failed: {e}")
        return {"status": "error", "message": f"update_interview failed: {str(e)}"}


async def create_diagnosis_session_mcp(actions: dict, flow_manager: FlowManager):
    """
    Create a diagnosis session linking real call session to diagnosis with dynamic IDs
    """
    try:
        call_session = flow_manager.state.get("call_session")
        current_interview = flow_manager.state.get("current_interview")

        if not call_session or not current_interview:
            logger.warning(
                "Missing call session or interview data for diagnosis session"
            )
            return {"status": "skipped", "message": "Missing required session data"}

        # Extract real call_id from call session response
        # Expected call_session format: {"status": "success", "message": "Call session started", "data": {"patient_id": 3, "start_time": "...", "call_id": 8, "created_at": "..."}}
        call_id = None
        if isinstance(call_session, dict):
            if "data" in call_session and isinstance(call_session["data"], dict):
                call_id = call_session["data"].get("call_id")
            else:
                call_id = call_session.get("call_id")

        # Extract real diagnosis_id from interview response
        # Expected interview format: {"patient_id": 3, "title": "...", "diagnosis_id": 3, "created_at": "..."}
        diagnosis_id = current_interview.get("diagnosis_id")

        if not call_id or not diagnosis_id:
            logger.error(
                f"Missing required IDs - call_id: {call_id}, diagnosis_id: {diagnosis_id}"
            )
            logger.debug(f"Call session data: {call_session}")
            logger.debug(f"Interview data: {current_interview}")
            return {
                "status": "error",
                "message": f"Missing IDs: call_id={call_id}, diagnosis_id={diagnosis_id}",
            }

        # Create diagnosis session with real IDs
        mcp_args = {
            "call_id": call_id,  # Real call_id from API (e.g., 8)
            "diagnosis_id": diagnosis_id,  # Real diagnosis_id from API (e.g., 3)
        }

        logger.info(
            f"Creating diagnosis session: call_id={call_id}, diagnosis_id={diagnosis_id}"
        )
        result = await mcp_client.call_tool("create_interview_session", mcp_args)

        if result:
            response = json.loads(result)

            # Store the diagnosis session response
            # Expected response: {"call_id": 4, "diagnosis_id": 3, "diagnosis_session_id": 4, "created_at": "2025-07-18T20:43:07"}
            flow_manager.state["diagnosis_session"] = response
            flow_manager.state["diagnosis_session_id"] = response.get(
                "diagnosis_session_id"
            )

            logger.info(
                f"Diagnosis session created: session_id={response.get('diagnosis_session_id')}"
            )

            return {
                "status": "success",
                "message": f"Diagnosis session {response.get('diagnosis_session_id')} created",
                "data": response,
            }
        else:
            raise Exception("No result from MCP create_interview_session")

    except Exception as e:
        logger.error(f"MCP create_interview_session failed: {e}")
        return {
            "status": "error",
            "message": f"create_interview_session failed: {str(e)}",
        }


# async def create_diagnosis_session_mcp(actions: dict, flow_manager: FlowManager):
#     """
#     Create a diagnosis session linking real call session to diagnosis with dynamic IDs
#     """
#     try:
#         call_session = flow_manager.state.get("call_session")
#         current_interview = flow_manager.state.get("current_interview")

#         if not call_session or not current_interview:
#             logger.warning(
#                 "Missing call session or interview data for diagnosis session"
#             )
#             return {"status": "skipped", "message": "Missing required session data"}

#         # Extract real call_id from call session response
#         call_id = None
#         if isinstance(call_session, dict):
#             if "data" in call_session and isinstance(call_session["data"], dict):
#                 call_id = call_session["data"].get("call_id")
#             else:
#                 call_id = call_session.get("call_id")

#         # Fallback to flow state
#         if not call_id:
#             call_id = flow_manager.state.get("call_id")

#         # Extract real diagnosis_id from interview response
#         diagnosis_id = current_interview.get("diagnosis_id")

#         if not call_id or not diagnosis_id:
#             logger.error(
#                 f"Missing required IDs - call_id: {call_id}, diagnosis_id: {diagnosis_id}"
#             )
#             logger.debug(f"Call session data: {call_session}")
#             logger.debug(f"Interview data: {current_interview}")
#             return {
#                 "status": "error",
#                 "message": f"Missing IDs: call_id={call_id}, diagnosis_id={diagnosis_id}",
#             }

#         # Create diagnosis session with real IDs
#         mcp_args = {
#             "call_id": call_id,
#             "diagnosis_id": diagnosis_id,
#         }

#         logger.info(
#             f"Creating diagnosis session: call_id={call_id}, diagnosis_id={diagnosis_id}"
#         )
#         result = await mcp_client.call_tool("create_interview_session", mcp_args)

#         if result:
#             response = json.loads(result)

#             # Store the diagnosis session response
#             flow_manager.state["diagnosis_session"] = response
#             flow_manager.state["diagnosis_session_id"] = response.get(
#                 "diagnosis_session_id"
#             )

#             logger.info(
#                 f"Diagnosis session created: session_id={response.get('diagnosis_session_id')}"
#             )

#             return {
#                 "status": "success",
#                 "message": f"Diagnosis session {response.get('diagnosis_session_id')} created",
#                 "data": response,
#             }
#         else:
#             raise Exception("No result from MCP create_interview_session")

#     except Exception as e:
#         logger.error(f"MCP create_interview_session failed: {e}")

#         # Create fallback diagnosis session
#         fallback_session = {
#             "call_id": call_id or 999,
#             "diagnosis_id": diagnosis_id or 1,
#             "diagnosis_session_id": 999,
#             "created_at": datetime.now().isoformat(),
#         }

#         flow_manager.state["diagnosis_session"] = fallback_session
#         flow_manager.state["diagnosis_session_id"] = 999

#         return {
#             "status": "fallback",
#             "message": f"Diagnosis session created with fallback due to error: {str(e)}",
#             "data": fallback_session,
#         }


async def create_chat_mcp_dynamic(
    call_id: int, speaker: str, message_text: str, flow_manager: FlowManager
):
    """
    Create chat message with dynamic call_id and real conversation content
    """
    try:
        # Use the provided parameters or extract from flow state
        if not call_id:
            call_session = flow_manager.state.get("call_session")
            if call_session and "data" in call_session:
                call_id = call_session["data"].get("call_id")

        if not call_id:
            logger.warning("No call_id available for chat creation")
            return {"status": "error", "message": "No call_id available"}

        mcp_args = {
            "call_id": call_id,
            "speaker": speaker,  # "user" or "assistant"
            "message_text": message_text,
        }

        logger.info(f"Creating chat message: call_id={call_id}, speaker={speaker}")
        result = await mcp_client.call_tool("create_chat", mcp_args)

        if result:
            response = json.loads(result)

            # Expected response: {"call_id": 4, "speaker": "user", "message_text": "Hello I am not feeling well!", "message_sequence": 4, "chat_id": 8, "created_at": "2025-07-18T20:38:06"}
            logger.info(
                f"Chat message created: chat_id={response.get('chat_id')}, sequence={response.get('message_sequence')}"
            )

            return {
                "status": "success",
                "message": f"Chat message {response.get('chat_id')} created",
                "data": response,
            }
        else:
            raise Exception("No result from MCP create_chat")

    except Exception as e:
        logger.error(f"MCP create_chat failed: {e}")
        return {"status": "error", "message": f"Create chat failed: {str(e)}"}


async def create_chat_mcp(actions: dict, flow_manager: FlowManager):
    """
    Create chat message with dynamic conversation data - for flow system actions
    """
    try:
        call_session = flow_manager.state.get("call_session")

        if not call_session:
            logger.warning("No active call session for chat creation")
            return {"status": "skipped", "message": "No active call session"}

        # Extract call_id from session data
        call_id = None
        if isinstance(call_session, dict) and "data" in call_session:
            call_id = call_session["data"].get("call_id")

        if not call_id:
            logger.warning("No call_id found for chat creation")
            return {"status": "error", "message": "No call_id available"}

        # Get the most recent conversation context
        context_messages = flow_manager.get_current_context()

        # Find the most recent user message to log as chat
        user_messages = [msg for msg in context_messages if msg.get("role") == "user"]
        assistant_messages = [
            msg for msg in context_messages if msg.get("role") == "assistant"
        ]

        # Create chat entries for recent conversation
        chat_entries_created = []

        # Log the most recent user message if available
        if user_messages:
            latest_user_msg = user_messages[-1]
            user_chat_result = await create_chat_mcp_dynamic(
                call_id=call_id,
                speaker="user",
                message_text=latest_user_msg.get("content", ""),
                flow_manager=flow_manager,
            )
            if user_chat_result.get("status") == "success":
                chat_entries_created.append(
                    f"User message: {user_chat_result['data'].get('chat_id')}"
                )

        # Log the most recent assistant message if available
        if assistant_messages:
            latest_assistant_msg = assistant_messages[-1]
            # Only log if it's actual content, not function calls
            content = latest_assistant_msg.get("content", "")
            if content and not content.startswith("{"):  # Avoid logging JSON responses
                assistant_chat_result = await create_chat_mcp_dynamic(
                    call_id=call_id,
                    speaker="assistant",
                    message_text=content,
                    flow_manager=flow_manager,
                )
                if assistant_chat_result.get("status") == "success":
                    chat_entries_created.append(
                        f"Assistant message: {assistant_chat_result['data'].get('chat_id')}"
                    )

        logger.info(
            f"Chat entries created for call_id {call_id}: {len(chat_entries_created)} messages"
        )

        return {
            "status": "success",
            "message": f"Chat conversation logged: {len(chat_entries_created)} messages",
            "chat_entries": chat_entries_created,
            "call_id": call_id,
        }

    except Exception as e:
        logger.error(f"MCP create_chat flow function failed: {e}")
        return {"status": "error", "message": f"Create chat failed: {str(e)}"}


# === TRANSITION FUNCTIONS ===


async def to_end_conversation(
    args: dict, flow_manager: FlowManager
) -> tuple[FlowResult, NodeConfig]:
    """Transition to end conversation node."""
    result = FlowResult(
        status="success",
        message="Transitioning to end conversation.",
    )
    next_node = create_end_conversation_node()
    return result, next_node


async def run_symptoms_intake_assessment(
    args: dict, flow_manager: FlowManager
) -> tuple[FlowResult, NodeConfig]:
    """Transition to symptoms assessment node."""
    result = FlowResult(
        status="success",
        message="Transitioning to symptoms assessment conversation.",
    )
    next_node = create_symptoms_assessment_node()
    return result, next_node


async def run_diagnosis_assessment(args: dict, flow_manager: FlowManager):
    """Transition to diagnosis assessment node."""
    result = FlowResult(
        status="success",
        message="Transitioning to diagnosis assessment conversation.",
    )
    next_node = create_diagnosis_assessment_node()
    return result, next_node


# === HELPER FUNCTIONS ===


async def check_state(args: dict, flow_manager: FlowManager):
    """Debug function to check conversation state."""
    state_info = {
        "flow_state": flow_manager.state,
        "current_node": flow_manager.current_node,
        "available_functions": (
            [f.name for f in flow_manager.current_functions]
            if hasattr(flow_manager, "current_functions")
            else []
        ),
    }

    logger.info(f"Conversation State: {state_info}")
    return state_info


def clean_prompt(text: str) -> str:
    clean_text = " ".join(text.split())
    return clean_text


# === NODE CONFIGURATIONS ===


def create_initial_node() -> NodeConfig:
    """
    Enhanced initial node with MCP functionality
    """
    return NodeConfig(
        name="introduction_node",
        role_messages=[
            {
                "role": "system",
                "content": clean_prompt(ROLE_MESSAGE),
            }
        ],
        task_messages=[
            {
                "role": "system",
                "content": clean_prompt(INITIAL_TASK_MESSAGE),
            }
        ],
        functions=[
            FlowsFunctionSchema(
                name="start_call_session",
                handler=start_call_session_mcp,
                description="Call this function to start the call session.",
                properties={
                    "patient_id": {
                        "type": "integer",
                        "description": "The patient ID for the call session",
                    }
                },
                required=["patient_id"],
            ),
            FlowsFunctionSchema(
                name="check_time",
                handler=check_time_mcp,
                description="Use this function to check the current time for greeting.",
                properties={},
                required=[],
            ),
            FlowsFunctionSchema(
                name="get_general_practice_information",
                handler=get_general_practice_information_mcp,
                description="Retrieves the GP information via MCP.",
                properties={},
                required=[],
            ),
            FlowsFunctionSchema(
                name="book_an_appointment",
                handler=book_an_appointment_mcp,
                description="Books an appointment via MCP.",
                properties={},
                required=[],
            ),
            FlowsFunctionSchema(
                name="get_patient_data",
                handler=get_patient_data_mcp,
                description="Retrieves patient personal information via MCP. Call this ONCE at the beginning.",
                properties={
                    "patient_id": {
                        "type": "integer",
                        "description": "The patient ID to retrieve data for",
                    }
                },
                required=["patient_id"],
            ),
            FlowsFunctionSchema(
                name="run_symptoms_intake_assessment",
                handler=run_symptoms_intake_assessment,
                description="Transitions to symptoms assessment when patient reports feeling unwell.",
                properties={},
                required=[],
            ),
        ],
    )


def create_symptoms_assessment_node() -> NodeConfig:
    """
    Enhanced symptoms assessment node with MCP functionality
    """
    return NodeConfig(
        name="symptoms_assessment_node",
        task_messages=[
            {
                "role": "system",
                "content": clean_prompt(SUGGEST_TASK_MESSAGE),
            },
        ],
        functions=[
            FlowsFunctionSchema(
                name="process_text",
                handler=process_text_mcp,
                description="MUST be called FIRST when patient mentions symptoms. Uses MCP to parse symptoms.",
                properties={
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
                required=["text", "age", "sex"],
            ),
            FlowsFunctionSchema(
                name="suggest_symptoms",
                handler=suggest_symptoms_mcp,
                description="Call AFTER process_text. Uses MCP to get suggested symptoms.",
                properties={
                    "age": {"type": "integer", "description": "Patient's age"},
                    "sex": {
                        "type": "string",
                        "description": "Patient's biological sex (male/female)",
                    },
                    "evidence": {
                        "type": "array",
                        "description": "List of evidence objects with id, choice_id, and source",
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
                        "description": "Whether to disable intimate content",
                        "default": False,
                    },
                },
                required=["age", "sex", "evidence"],
            ),
            FlowsFunctionSchema(
                name="create_diagnosis_session",
                handler=create_diagnosis_session_mcp,
                description="Use this function to create the diagnosis session.",
                properties={
                    "call_id": {
                        "type": "integer",
                        "description": "The ID of the call session",
                    },
                    "diagnosis_id": {
                        "type": "integer",
                        "description": "The ID of the diagnosis to link",
                    },
                },
                required=["diagnosis_id", "call_id"],
            ),
            FlowsFunctionSchema(
                name="create_interview",
                handler=create_interview_mcp,
                description="Use this function to start the interview.",
                properties={
                    "title": {
                        "type": "string",
                        "description": "The title of the interview.",
                    },
                    "description": {
                        "type": "string",
                        "description": "The brief description of an interview.",
                    },
                    "report": {
                        "type": "string",
                        "description": "Detailed report of the interview. This is expected to be a JSON string.",
                    },
                },
                required=["title", "description", "report"],
            ),
            FlowsFunctionSchema(
                name="update_interview",
                handler=update_interview_mcp,
                description="Use this function to update the interview.",
                properties={
                    "diagnosis_id": {
                        "type": "integer",
                        "description": "The Diagnosis ID.",
                    },
                    "title": {
                        "type": "string",
                        "description": "The title of the interview.",
                    },
                    "description": {
                        "type": "string",
                        "description": "The brief description of an interview.",
                    },
                    "report": {
                        "type": "string",
                        "description": "Detailed report of the interview. This is expected to be a JSON string.",
                    },
                },
                required=["diagnosis_id", "title", "description", "report"],
            ),
            FlowsFunctionSchema(
                name="store_evidence",
                handler=store_evidence_mcp,
                description="ONLY call AFTER patient CONFIRMS they have a symptom. Uses MCP to store evidence.",
                properties={
                    "id": {
                        "type": "string",
                        "description": "The symptom ID from the suggested symptoms list",
                    },
                    "choice_id": {
                        "type": "string",
                        "enum": ["present", "absent", "unknown"],
                        "description": "Whether symptom is present or absent or unknown",
                    },
                    "source": {
                        "type": "string",
                        "enum": ["suggest"],
                        "description": "Source of the symptom evidence",
                    },
                },
                required=["id", "choice_id", "source"],
            ),
            FlowsFunctionSchema(
                name="run_diagnosis_assessment",
                handler=run_diagnosis_assessment,
                description="Transitions to diagnosis assessment.",
                properties={},
                required=[],
            ),
        ],
        pre_actions=[
            ActionConfig(type="function", handler=create_interview_mcp),
            ActionConfig(type="function", handler=create_diagnosis_session_mcp),
        ],
        post_actions=[
            ActionConfig(type="function", handler=store_evidence_to_state),
            ActionConfig(type="function", handler=update_interview_mcp),
        ],
    )


def create_diagnosis_assessment_node() -> NodeConfig:
    """
    Enhanced diagnosis assessment node with MCP functionality
    """
    return NodeConfig(
        name="diagnosis_assessment_node",
        task_messages=[
            {
                "role": "system",
                "content": clean_prompt(DIAGNOSIS_TASK_MESSAGE_V02),
            },
        ],
        functions=[
            FlowsFunctionSchema(
                name="run_diagnosis",
                handler=run_diagnosis_mcp,
                description="Gets the next question for diagnosis interview via MCP.",
                properties={
                    "age": {"type": "integer", "description": "Patient's age"},
                    "sex": {
                        "type": "string",
                        "description": "Patient's biological sex (male/female)",
                    },
                    "evidence": {
                        "type": "array",
                        "description": "List of evidence objects with id, choice_id, and source",
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
                        "description": "Whether to disable intimate content",
                        "default": False,
                    },
                },
                required=["age", "sex", "evidence"],
            ),
            FlowsFunctionSchema(
                name="create_interview",
                handler=create_interview_mcp,
                description="Use this function to start the interview.",
                properties={
                    "title": {
                        "type": "string",
                        "description": "The title of the interview.",
                    },
                    "description": {
                        "type": "string",
                        "description": "The brief description of an interview.",
                    },
                    "report": {
                        "type": "string",
                        "description": "Detailed report of the interview. This is expected to be a JSON string.",
                    },
                },
                required=["title", "description", "report"],
            ),
            FlowsFunctionSchema(
                name="update_interview",
                handler=update_interview_mcp,
                description="Use this function to update the interview.",
                properties={
                    "diagnosis_id": {
                        "type": "integer",
                        "description": "The Diagnosis ID.",
                    },
                    "title": {
                        "type": "string",
                        "description": "The title of the interview.",
                    },
                    "description": {
                        "type": "string",
                        "description": "The brief description of an interview.",
                    },
                    "report": {
                        "type": "string",
                        "description": "Detailed report of the interview. This is expected to be a JSON string.",
                    },
                },
                required=["diagnosis_id", "title", "description", "report"],
            ),
            FlowsFunctionSchema(
                name="store_evidence",
                handler=store_evidence_mcp,
                description="Uses MCP to store evidence after patient confirms symptoms.",
                properties={
                    "id": {
                        "type": "string",
                        "description": "The symptom ID",
                    },
                    "choice_id": {
                        "type": "string",
                        "enum": ["present", "absent", "unknown"],
                        "description": "Whether symptom is present or absent or unknown",
                    },
                    "source": {
                        "type": "string",
                        "description": "Source of the symptom evidence",
                    },
                },
                required=["id", "choice_id"],
            ),
        ],
        post_actions=[ActionConfig(type="function", handler=update_interview_mcp)],
    )


def create_end_conversation_node() -> NodeConfig:
    """End conversation node."""
    return NodeConfig(
        name="end_conversation_node",
        task_messages=[
            {
                "role": "system",
                "content": """
                Thank the patient warmly and mention they can call back anytime if they need more help.
                Then call end_call_session function to end the call session.
                """,
            }
        ],
        functions=[
            FlowsFunctionSchema(
                name="end_call_session",
                handler=end_call_session_mcp,
                description="Use this function to end the call session.",
                properties={
                    "call_id": {
                        "type": "integer",
                        "description": "The ID of the call session to terminate",
                    }
                },
                required=["call_id"],
            ),
        ],
        post_actions=[ActionConfig(type="end_conversation")],
    )


def create_debug_node() -> NodeConfig:
    """Debug node to inspect MCP tools and state."""
    debug_functions = [
        FlowsFunctionSchema(
            name="list_mcp_tools",
            handler=lambda **kwargs: mcp_client.get_tools_info(),
            description="List all available MCP tools and their information",
            properties={},
            required=[],
        ),
        FlowsFunctionSchema(
            name="check_state",
            handler=check_state,
            description="Get current flow state and node information",
            properties={},
            required=[],
        ),
    ]

    return NodeConfig(
        name="debug_node",
        task_messages=[
            {
                "role": "system",
                "content": "Debug mode: You can inspect MCP tools and conversation state.",
            }
        ],
        functions=debug_functions,
    )


# === MAIN APPLICATION ===


def create_tts_service():
    """Create TTS service with fallback options"""
    try:
        # Try ElevenLabs first
        logger.info("Attempting to initialize ElevenLabs TTS...")
        tts = ElevenLabsTTSService(
            model=tts_model,
            api_key=elevenlabs_api_key,
            voice_id=elevenlabs_voice_id,
            text_filters=[MarkdownTextFilter()],
        )
        logger.info("ElevenLabs TTS initialized successfully")
        return tts

    except Exception as e:
        logger.warning(f"ElevenLabs TTS failed: {e}")
        logger.info("Falling back to OpenAI TTS...")

        # Fallback to OpenAI TTS
        from pipecat.services.openai.tts import OpenAITTSService

        return OpenAITTSService(
            api_key=openai_api_key,
            model="gpt-4o-mini-tts",
            voice="nova",
            instructions="Speak in a empathetic and positive tone.",
        )


async def main(room_url: str, token: str):
    """
    Main application entry point with robust MCP integration.
    """
    session = None  # Initialize session variable at the start

    try:
        logger.info("Initializing MCP client...")

        try:
            # Use timeout to prevent hanging
            success = await asyncio.wait_for(
                mcp_client.initialize("core/mcp_server.py"),
                timeout=15.0,  # Increased timeout
            )

            if success and mcp_client.is_initialized:
                tools_info = mcp_client.get_tools_info()
                logger.info(
                    f"MCP Server connected! Available tools: {tools_info['total_tools']}"
                )
                for tool in tools_info["tools"]:
                    logger.debug(f"  - {tool['name']}: {tool['description'][:50]}...")
            else:
                logger.warning("MCP initialization failed, continuing without MCP")

        except asyncio.TimeoutError:
            logger.warning("MCP initialization timed out, continuing without MCP")
        except Exception as e:
            logger.error(f"MCP setup failed: {e}")
            logger.warning("Continuing without MCP integration")

        # Initialize Pipecat components
        session = aiohttp.ClientSession()

        # Configure transport
        transport = DailyTransport(
            room_url,
            token,
            "GP Front Desk Assistant",
            DailyParams(
                audio_in_enabled=True,
                audio_out_enabled=True,
                vad_analyzer=SileroVADAnalyzer(),
                transcription_enabled=True,
            ),
        )

        # Configure LLM
        llm = OpenAILLMService(
            api_key=openai_api_key,
            model=llm_model,
            params=OpenAILLMService.InputParams(
                max_tokens=200,  # Increased for better responses
                top_p=0.9,
                temperature=0.2,
            ),
        )

        # Configure STT
        stt = OpenAISTTService(
            api_key=openai_api_key,
            model=stt_model,
        )

        # Configure TTS
        # tts = create_tts_service()
        tts = OpenAITTSService(
            api_key=openai_api_key,
            model="gpt-4o-mini-tts",
            voice="nova",
            instructions="Speak in a empathetic and positive tone.",
        )

        # Setup conversation context
        messages = []
        context = OpenAILLMContext(messages)
        context_aggregator = llm.create_context_aggregator(context)

        # Create the duplicate response filter
        duplicate_response_filter = create_simple_sentence_filter()

        # Build pipeline
        pipeline = Pipeline(
            [
                transport.input(),
                stt,
                context_aggregator.user(),
                llm,
                duplicate_response_filter,
                tts,
                transport.output(),
                context_aggregator.assistant(),
            ]
        )

        # Create task
        task = PipelineTask(
            pipeline,
            params=PipelineParams(
                allow_interruptions=True,
                enable_metrics=True,
                enable_usage_metrics=True,
            ),
            enable_tracing=True,
            enable_turn_tracking=True,
            enable_watchdog_logging=True,
        )

        # Create flow manager
        flow_manager = FlowManager(
            task=task,
            llm=llm,
            context_aggregator=context_aggregator,
            transport=transport,
        )

        # Event handler for participant joining
        @transport.event_handler("on_first_participant_joined")
        async def on_first_participant_joined(transport, participant):
            logger.info(f"Participant joined: {participant}")
            await transport.capture_participant_transcription(participant["id"])

            # Initialize with MCP-enhanced node
            await flow_manager.initialize(create_initial_node())
            logger.info("Conversation flow initialized with MCP integration")

        # When the participant leaves, we exit the bot.
        @transport.event_handler("on_participant_left")
        async def on_participant_left(transport, participant, reason):
            await task.queue_frame(EndFrame())

        # If the call is ended make sure we quit as well.
        @transport.event_handler("on_call_state_updated")
        async def on_call_state_updated(transport, state):
            if state == "left":
                await task.queue_frame(EndFrame())

        # FIXED: Create custom PipelineRunner that handles threading issues
        try:
            # Check if we're in the main thread
            is_main_thread = threading.current_thread() is threading.main_thread()
            logger.info(f"Running in main thread: {is_main_thread}")

            if is_main_thread:
                # Use normal PipelineRunner
                runner = PipelineRunner()
            else:
                # Create a custom runner without signal handling
                runner = SafePipelineRunner()

            await runner.run(task)

        except ValueError as e:
            if "add_signal_handler" in str(e):
                logger.warning(
                    "Signal handler setup failed, using alternative approach"
                )
                # Fallback: Run without PipelineRunner
                await task.run()
            else:
                raise

    except Exception as e:
        logger.error(f"Application failed: {e}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
        raise
    finally:
        # Clean up resources - check if session exists before closing
        if session is not None:
            try:
                await session.close()
            except Exception as e:
                logger.warning(f"Error closing session: {e}")

        # Clean up MCP resources
        logger.info("Cleaning up MCP client...")
        try:
            await mcp_client.cleanup()
        except Exception as e:
            logger.warning(f"MCP cleanup error: {e}")


class SafePipelineRunner:
    """
    Custom PipelineRunner that doesn't set up signal handlers.
    Safe for use in non-main threads and serverless environments.
    """

    def __init__(self):
        self._shutdown_event = asyncio.Event()

    async def run(self, task):
        """Run the pipeline task without signal handling"""
        try:
            logger.info("Starting pipeline with SafePipelineRunner")
            await task.run()
        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}")
            raise
        finally:
            logger.info("Pipeline execution completed")
