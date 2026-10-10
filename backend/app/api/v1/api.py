from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth, 
    users, 
    patients, 
    care_levels, 
    call_sessions, 
    chat_history, 
    diagnoses, 
    diagnosis_sessions, 
    triage_assessments
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(patients.router, prefix="/patients", tags=["patients"])
api_router.include_router(care_levels.router, prefix="/care-levels", tags=["care levels"])
api_router.include_router(call_sessions.router, prefix="/call-sessions", tags=["call sessions"])
api_router.include_router(chat_history.router, prefix="/chat-history", tags=["chat history"])
api_router.include_router(diagnoses.router, prefix="/diagnoses", tags=["diagnoses"])
api_router.include_router(diagnosis_sessions.router, prefix="/diagnosis-sessions", tags=["diagnosis sessions"])
api_router.include_router(triage_assessments.router, prefix="/triage-assessments", tags=["triage assessments"]) 