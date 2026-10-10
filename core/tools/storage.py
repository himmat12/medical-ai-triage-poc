"""
GP Frontdesk data storage tool (database).
"""

import asyncio

from time import sleep
from pipecat_flows import FlowManager
from typing import Dict, Any, Optional


def is_patient_data_available(flag: bool) -> bool:
    """
    Method that will return bool value based on the status of te patient data database - either completed -> `True` or, `False`.
    """
    return flag


async def fetch_patient_data(
    action: Dict[str, Any] = None,
    flow_manager: Optional[FlowManager] = None,
):
    """
    Method to retrive patients personal data from database.
    """
    print("fetching patient data ...")

    await asyncio.sleep(0.2)  # mocking 200ms average network latency in API calls

    if flow_manager and hasattr(flow_manager, "state"):
        flow_manager.state["patient_data"] = {
            "patient_id": "p_001",
            "name": "Himmat Rai",
            "age": 26,
            "date_of_birth": "18/05/1999",
            "sex": "male",
            "phone": "9860867234",
            "address": "Bede Hall, Le2 7EQ, Leicester",
            "emergency_contact_name": "John Rai",
            "emergency_contact_phone": "9860876534",
            "symptoms": [],
            "conditions": [],
            "created_at": "",
            "updated_at": "",
        }
    
    if flow_manager and hasattr(flow_manager, 'state'):
        print(flow_manager.state.get("patient_data"))
        return flow_manager.state.get("patient_data")
    return None
