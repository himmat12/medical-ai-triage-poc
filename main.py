import asyncio
import os
import sys
import requests
import time

from loguru import logger
from dotenv import load_dotenv

from core.mcp_client import mcp_client
from core.bot import main


load_dotenv(override=True)

# Environment credentials
openai_api_key = os.environ.get("OPENAI_API_KEY")
llm_model = os.environ.get("LLM_MODEL")
tts_model = os.environ.get("TTS_MODEL")
stt_model = os.environ.get("STT_MODEL")
elevenlabs_api_key = os.environ.get("ELEVENLABS_API_KEY")
elevenlabs_voice_id = os.environ.get("ELEVENLABS_VOICE_ID")
daily_access_token = os.environ.get("DAILY_API_KEY")


def setup_logging():
    """Setup logging that works in any environment"""
    logger.remove()  # This removes ALL handlers safely
    logger.add(
        sys.stderr,
        level="DEBUG",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | {message}",
        colorize=True,
    )


setup_logging()


def debug_environment():
    """
    Debug function to check available environment variables in Cerebrium
    """
    try:
        # Check which environment variables are available
        required_vars = [
            # OpenAI
            "OPENAI_API_KEY",
            "GEMINI_API_KEY",
            # ElevenLabs
            "ELEVENLABS_API_KEY",
            "ELEVENLABS_VOICE_ID",
            # Bot Implementation
            "BOT_IMPLEMENTATION",
            # Cartesia
            "CARTESIA_API_KEY",
            "CARTESIA_VOICE_ID",
            # Daily
            "DAILY_API_KEY",
            "DAILY_ROOM_URL",
            "DAILY_TOKEN",
            # Infermedica
            "INFRAMEDICA_APP_ID",
            "INFRAMEDICA_APP_KEY",
            "INFRAMEDICA_BASE_URL",
            # Mem0
            "MEM0_API_KEY",
            # Models Config
            "LLM_MODEL",
            "TTS_MODEL",
            "STT_MODEL",
            # Database Backend
            "DATABASE_URL",
            "SECRET_KEY",
            "ALGORITHM",
            "ACCESS_TOKEN_EXPIRE_MINUTES",
            # Backend Service API
            "BACKEND_BASE_URL",
            "BACKEND_API_ROUTER",
            "ACCESS_TOKEN",
            "USERNAME",
            "PASSWORD",
        ]

        env_status = {}
        for var in required_vars:
            value = os.environ.get(var)
            if value:
                # Show first 8 characters for security
                masked_value = value[:8] + "..." if len(value) > 8 else value
                env_status[var] = {
                    "available": True,
                    "preview": masked_value,
                    "length": len(value),
                }
            else:
                env_status[var] = {"available": False, "preview": None, "length": 0}

        # Also check all environment variables that start with common prefixes
        all_env = dict(os.environ)
        relevant_env = {
            k: "***"
            for k, v in all_env.items()
            if any(
                prefix in k.upper()
                for prefix in [
                    "OPENAI",
                    "GEMINI",
                    "ELEVEN",
                    "BOT_",
                    "CARTESIA",
                    "DAILY",
                    "INFRAMEDICA",
                    "INFERMEDICA",
                    "MEM0",
                    "LLM_",
                    "TTS_",
                    "STT_",
                    "DATABASE",
                    "SECRET",
                    "ALGORITHM",
                    "ACCESS_TOKEN",
                    "BASE_URL",
                    "USERNAME",
                    "PASSWORD",
                    "EXPIRE",
                ]
            )
        }

        # Group environment variables by category for better organization
        categorized_env = {
            "openai": {},
            "elevenlabs": {},
            "cartesia": {},
            "daily": {},
            "infermedica": {},
            "mem0": {},
            "models": {},
            "database": {},
            "backend_api": {},
            "other": {},
        }

        for var_name, status in env_status.items():
            var_upper = var_name.upper()
            if "OPENAI" in var_upper or "GEMINI" in var_upper:
                categorized_env["openai"][var_name] = status
            elif "ELEVEN" in var_upper:
                categorized_env["elevenlabs"][var_name] = status
            elif "CARTESIA" in var_upper:
                categorized_env["cartesia"][var_name] = status
            elif "DAILY" in var_upper:
                categorized_env["daily"][var_name] = status
            elif "INFRAMEDICA" in var_upper or "INFERMEDICA" in var_upper:
                categorized_env["infermedica"][var_name] = status
            elif "MEM0" in var_upper:
                categorized_env["mem0"][var_name] = status
            elif any(model in var_upper for model in ["LLM_", "TTS_", "STT_"]):
                categorized_env["models"][var_name] = status
            elif any(
                db in var_upper for db in ["DATABASE", "SECRET", "ALGORITHM", "EXPIRE"]
            ):
                categorized_env["database"][var_name] = status
            elif any(
                api in var_upper
                for api in ["BASE_URL", "ACCESS_TOKEN", "USERNAME", "PASSWORD"]
            ):
                categorized_env["backend_api"][var_name] = status
            elif "BOT_IMPLEMENTATION" in var_upper:
                categorized_env["other"][var_name] = status
        return {
            "status": "success",
            "required_variables": env_status,
            "categorized_variables": categorized_env,
            "all_relevant_variables": relevant_env,
            "total_env_vars": len(all_env),
            "missing_variables": [
                var for var, status in env_status.items() if not status["available"]
            ],
            "available_variables": [
                var for var, status in env_status.items() if status["available"]
            ],
            "python_path": os.environ.get("PYTHONPATH"),
            "working_directory": os.getcwd(),
        }

    except Exception as e:
        return {"status": "error", "message": str(e), "working_directory": os.getcwd()}


async def check_api_health():
    """
    Enhanced patient data retrieval using MCP
    """
    try:
        await asyncio.wait_for(
            mcp_client.initialize("core/mcp_server.py"),
            timeout=15.0,  # Increased timeout
        )

        # Call MCP server tool instead of local implementation
        result = await mcp_client.call_tool("check_health", {})

        logger.info(f"MCP health check response: {result}")

        if result:
            import json

            patient_data = json.loads(result)
            logger.info("Backend API health check via MCP")
            return patient_data

    except Exception as e:
        logger.error(f"MCP health check failed: {e}")

        return {
            "status": "failed",
            "message": "Health check failed.",
            "error": e.__str__(),
        }


async def get_patient_data_test():
    """
    Enhanced patient data retrieval using MCP
    """
    try:
        await asyncio.wait_for(
            mcp_client.initialize("core/mcp_server.py"),
            timeout=15.0,  # Increased timeout
        )

        # Call MCP server tool instead of local implementation
        result = await mcp_client.call_tool(
            "get_patient_data",
            # the patient_id value will be dynamic when the mobile app is developed and passed through an api endpoint
            {"patient_id": 3},
        )

        if result:
            import json

            patient_data = json.loads(result)
            logger.info("Patient data retrieved via MCP")
            return patient_data

    except Exception as e:
        logger.error(f"MCP patient data retrieval failed: {e}")
        # Fallback to local implementation

        return {
            "status": "failed",
            "message": "Failed to retrive patient data.",
        }


# bot entry point where it receives the client room url  and initializes
# and join the room and the bot is live and user can interact with bot
async def run(room_url: str, token: str, run_id=None):
    # async def run(run_id=None):
    try:
        # room = create_room()
        # room_url = room["url"]
        # token = room["token"]
        result = await main(room_url, token)
        return {
            "status": "success",
            "message": "Voice agent completed",
            "result": result,
            # "room_url": room_url,
            "run_id": run_id,
        }
    except Exception as e:
        logger.error(f"Voice agent failed: {e}")
        return {"status": "error", "message": str(e), "run_id": run_id}


def create_room():
    url = "https://api.daily.co/v1/rooms/"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {daily_access_token}",
    }
    data = {
        "properties": {
            "exp": int(time.time()) + 60 * 48,  # 2 days
            "eject_at_room_exp": True,
        }
    }

    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        room_info = response.json()
        token = create_token(room_info["name"])
        if token and "token" in token:
            room_info["token"] = token["token"]
        else:
            logger.error("Failed to create token")
            return {
                "message": "There was an error creating your room",
                "status_code": 500,
            }
        return room_info
    else:
        logger.error(f"Failed to create room: {response.status_code}")
        return {"message": "There was an error creating your room", "status_code": 500}


def create_token(room_name: str = "default-room"):
    url = "https://api.daily.co/v1/meeting-tokens"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {daily_access_token}",
    }
    data = {"properties": {"room_name": room_name, "is_owner": True}}

    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        token_info = response.json()
        return token_info
    else:
        logger.error(f"Failed to create token: {response.status_code}")
        return None


# for local development
if __name__ == "__main__":
    room_info = create_room()
    print(f"Join room: {room_info}")
    print(f"Join room: {room_info["url"]}")
    asyncio.run(main(room_info["url"], room_info["token"]))
