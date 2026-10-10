# DEPRICATED: NOT IN USE ANYMORE

"""
Infremedica Engine API services tools
"""

import requests
import os

from typing import Optional, Any, Dict, List
from dotenv import load_dotenv
from uuid import uuid4



load_dotenv(override=True)

base_url = os.environ.get("INFRAMEDICA_BASE_URL")

app_id = os.environ.get("INFRAMEDICA_APP_ID")
app_key = os.environ.get("INFRAMEDICA_APP_KEY")

if not app_id or not app_key:
    raise ValueError(
        "Missing required environment variables: INFRAMEDICA_APP_ID or INFRAMEDICA_APP_KEY"
    )

interview_id: Optional[str] = None


def generate_interview_id():
    """
    Generate random secure Interview ID. This persists throughout the interview session
    and should be discarded after the interview ends.
    """
    interview_id = uuid4().__str__()
    print(interview_id)


def search_concepts(phrase: str, age: int, sex: str):
    """
    Search known medical concepts from Infermedica knowledge library.

    Args:
        phrase: Medical phrase to search for
        age: Patient's age
        sex: Patient's biological sex ('male' or 'female')

    Returns:
        Search results from API

    Raises:
        InfermedicaAPIError: For API-related errors
        ValueError: For invalid parameters
    """

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
        respone = requests.get(
            f"{base_url}/search",
            params=params,
            headers=headers,
        )
        respone.raise_for_status()

        if respone.status_code == 200:
            return respone.json()

    except BaseException as err:
        return f"ERROR: {err}"


def parse_text(text: str, age: int, sex: str):
    """
    NLP service for parsing natural text from patients to identify medical concepts
    (symptoms, conditions, and risk factors).

    Args:
        text: Patient's natural language input
        age: Patient's age
        sex: Patient's biological sex

    Returns:
        Parsed response data or None if request fails

    Raises:
        requests.RequestException: For HTTP-related errors
        ValueError: For missing environment variables
    """

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
        return response.json()

    except requests.RequestException as e:
        print(f"ERROR: {e}")
        return None


def suggest(
    age: int,
    sex: str,
    evidence: List[Dict[str, str]],
    disable_intimate_content: bool = False,
):
    """
    Method to refine the initial observation (symptoms, and conditions).
    """
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
            f"{base_url}/suggest?max_results=2",
            headers=headers,
            json=payload,
        )

        response.raise_for_status()
        return response.json()

    except requests.RequestException as e:
        print(f"ERROR: {e}")
        return None


def diagnosis(
    age: int,
    sex: str,
    evidence: List[Dict[str, str]],
    disable_intimate_content: bool = False,
):
    """
    Method to diagnosis the patient based on the initial observations and symptoms.
    """
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
            # "disable_groups": True,
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
        return response.json()

    except requests.RequestException as e:
        print(f"ERROR: {e}")
        return None


# generate_interview_id()

# res01 = parse_text("I have a vomit and feever, and diarreah", 26, "male")
# res02 = search_concepts("I have a vomit and feever, and diarreah", 26, "male")

# suggest_evidence = [
#     {
#         "choice_id": "present",
#         "id": "s_39",
#         "source": "initial",
#     },
#     {
#         "choice_id": "present",
#         "id": "s_305",
#         "source": "initial",
#     },
#     {
#         "choice_id": "present",
#         "id": "s_98",
#         "source": "initial",
#     },
#     {
#         "choice_id": "present",
#         "id": "s_8",
#         "source": "initial",
#     },
# ]

# res03 = suggest(25, "male", suggest_evidence)

# diagnosis_evidence = [
#     {
#         "choice_id": "present",
#         "id": "s_39",
#         "source": "initial",
#     },
#     {
#         "choice_id": "present",
#         "id": "s_305",
#         "source": "initial",
#     },
#     {
#         "choice_id": "present",
#         "id": "s_98",
#         "source": "initial",
#     },
#     {
#         "choice_id": "present",
#         "id": "s_8",
#         "source": "initial",
#     },
#     {
#         "choice_id": "present",
#         "id": "s_216",
#         "source": "suggest",
#     },
#     {
#         "choice_id": "present",
#         "id": "s_284",
#         "source": "suggest",
#     },
# ]


# res04 = diagnosis(25, "male", diagnosis_evidence)

# print(res01)
# print(res02)
# print(res03)
# print(res04)
