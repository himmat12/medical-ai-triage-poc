from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user
from app.crud import call_session as crud_call_session
from app.models.user import User
from app.schemas.call_session import CallSession, CallSessionCreate, CallSessionUpdate

router = APIRouter()


@router.get("/", response_model=List[CallSession])
def read_call_sessions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve call sessions
    """
    call_sessions = crud_call_session.get_call_sessions(db, skip=skip, limit=limit)
    return call_sessions


@router.post("/", response_model=CallSession)
def create_call_session(
    *,
    db: Session = Depends(get_db),
    call_session_in: CallSessionCreate,
    current_user: User = Depends(get_current_user),
):
    """
    Create new call session
    """
    # Check if patient has an active call session
    active_session = crud_call_session.get_active_call_session(db, call_session_in.patient_id)
    if active_session:
        raise HTTPException(
            status_code=400,
            detail="Patient already has an active call session"
        )
    
    call_session = crud_call_session.create_call_session(db, call_session_in)
    return call_session


@router.get("/{call_id}", response_model=CallSession)
def read_call_session(
    *,
    db: Session = Depends(get_db),
    call_id: int,
    current_user: User = Depends(get_current_user),
):
    """
    Get call session by ID
    """
    call_session = crud_call_session.get_call_session(db, call_id)
    if not call_session:
        raise HTTPException(status_code=404, detail="Call session not found")
    return call_session


@router.put("/{call_id}", response_model=CallSession)
def update_call_session(
    *,
    db: Session = Depends(get_db),
    call_id: int,
    call_session_in: CallSessionUpdate,
    current_user: User = Depends(get_current_user),
):
    """
    Update call session
    """
    call_session = crud_call_session.update_call_session(db, call_id, call_session_in)
    if not call_session:
        raise HTTPException(status_code=404, detail="Call session not found")
    return call_session


@router.post("/{call_id}/end", response_model=CallSession)
def end_call_session(
    *,
    db: Session = Depends(get_db),
    call_id: int,
    current_user: User = Depends(get_current_user),
):
    """
    End call session
    """
    call_session = crud_call_session.end_call_session(db, call_id)
    if not call_session:
        raise HTTPException(status_code=404, detail="Call session not found")
    return call_session


@router.get("/patient/{patient_id}", response_model=List[CallSession])
def read_call_sessions_by_patient(
    *,
    db: Session = Depends(get_db),
    patient_id: int,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
):
    """
    Get call sessions for a specific patient
    """
    call_sessions = crud_call_session.get_call_sessions_by_patient(db, patient_id, skip=skip, limit=limit)
    return call_sessions


@router.get("/patient/{patient_id}/active", response_model=CallSession)
def read_active_call_session(
    *,
    db: Session = Depends(get_db),
    patient_id: int,
    current_user: User = Depends(get_current_user),
):
    """
    Get active call session for a patient
    """
    call_session = crud_call_session.get_active_call_session(db, patient_id)
    if not call_session:
        raise HTTPException(status_code=404, detail="No active call session found for this patient")
    return call_session


@router.delete("/{call_id}")
def delete_call_session(
    *,
    db: Session = Depends(get_db),
    call_id: int,
    current_user: User = Depends(get_current_user),
):
    """
    Delete call session
    """
    deleted = crud_call_session.delete_call_session(db, call_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Call session not found")
    return {"message": "Call session deleted successfully"} 