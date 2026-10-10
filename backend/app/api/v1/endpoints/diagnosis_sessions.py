from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user
from app.crud import diagnosis_session as crud_diagnosis_session
from app.models.user import User
from app.schemas.diagnosis_session import DiagnosisSession, DiagnosisSessionCreate, DiagnosisSessionUpdate

router = APIRouter()


@router.get("/", response_model=List[DiagnosisSession])
def read_diagnosis_sessions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve diagnosis sessions
    """
    diagnosis_sessions = crud_diagnosis_session.get_diagnosis_sessions(db, skip=skip, limit=limit)
    return diagnosis_sessions


@router.post("/", response_model=DiagnosisSession)
def create_diagnosis_session(
    *,
    db: Session = Depends(get_db),
    diagnosis_session_in: DiagnosisSessionCreate,
    current_user: User = Depends(get_current_user),
):
    """
    Create new diagnosis session
    """
    # Check if this combination already exists
    existing_session = crud_diagnosis_session.get_diagnosis_session_by_call_and_diagnosis(
        db, diagnosis_session_in.call_id, diagnosis_session_in.diagnosis_id
    )
    if existing_session:
        raise HTTPException(
            status_code=400,
            detail="Diagnosis session already exists for this call and diagnosis"
        )
    
    diagnosis_session = crud_diagnosis_session.create_diagnosis_session(db, diagnosis_session_in)
    return diagnosis_session


@router.get("/{diagnosis_session_id}", response_model=DiagnosisSession)
def read_diagnosis_session(
    *,
    db: Session = Depends(get_db),
    diagnosis_session_id: int,
    current_user: User = Depends(get_current_user),
):
    """
    Get diagnosis session by ID
    """
    diagnosis_session = crud_diagnosis_session.get_diagnosis_session(db, diagnosis_session_id)
    if not diagnosis_session:
        raise HTTPException(status_code=404, detail="Diagnosis session not found")
    return diagnosis_session


@router.put("/{diagnosis_session_id}", response_model=DiagnosisSession)
def update_diagnosis_session(
    *,
    db: Session = Depends(get_db),
    diagnosis_session_id: int,
    diagnosis_session_in: DiagnosisSessionUpdate,
    current_user: User = Depends(get_current_user),
):
    """
    Update diagnosis session
    """
    diagnosis_session = crud_diagnosis_session.update_diagnosis_session(
        db, diagnosis_session_id, diagnosis_session_in
    )
    if not diagnosis_session:
        raise HTTPException(status_code=404, detail="Diagnosis session not found")
    return diagnosis_session


@router.get("/call/{call_id}", response_model=List[DiagnosisSession])
def read_diagnosis_sessions_by_call(
    *,
    db: Session = Depends(get_db),
    call_id: int,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
):
    """
    Get diagnosis sessions for a specific call
    """
    diagnosis_sessions = crud_diagnosis_session.get_diagnosis_sessions_by_call(
        db, call_id, skip=skip, limit=limit
    )
    return diagnosis_sessions


@router.get("/diagnosis/{diagnosis_id}", response_model=List[DiagnosisSession])
def read_diagnosis_sessions_by_diagnosis(
    *,
    db: Session = Depends(get_db),
    diagnosis_id: int,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
):
    """
    Get diagnosis sessions for a specific diagnosis
    """
    diagnosis_sessions = crud_diagnosis_session.get_diagnosis_sessions_by_diagnosis(
        db, diagnosis_id, skip=skip, limit=limit
    )
    return diagnosis_sessions


@router.delete("/{diagnosis_session_id}")
def delete_diagnosis_session(
    *,
    db: Session = Depends(get_db),
    diagnosis_session_id: int,
    current_user: User = Depends(get_current_user),
):
    """
    Delete diagnosis session
    """
    deleted = crud_diagnosis_session.delete_diagnosis_session(db, diagnosis_session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Diagnosis session not found")
    return {"message": "Diagnosis session deleted successfully"} 