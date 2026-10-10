from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.call_session import CallSession
from app.schemas.call_session import CallSessionCreate, CallSessionUpdate


def get_call_session(db: Session, call_id: int) -> Optional[CallSession]:
    return db.query(CallSession).filter(CallSession.call_id == call_id).first()


def get_call_sessions(db: Session, skip: int = 0, limit: int = 100) -> List[CallSession]:
    return db.query(CallSession).offset(skip).limit(limit).all()


def get_call_sessions_by_patient(db: Session, patient_id: int, skip: int = 0, limit: int = 100) -> List[CallSession]:
    return db.query(CallSession).filter(CallSession.patient_id == patient_id).offset(skip).limit(limit).all()


def get_active_call_session(db: Session, patient_id: int) -> Optional[CallSession]:
    """Get the currently active call session for a patient (end_time is null)"""
    return db.query(CallSession).filter(
        CallSession.patient_id == patient_id,
        CallSession.end_time == None
    ).first()


def create_call_session(db: Session, call_session: CallSessionCreate) -> CallSession:
    db_call_session = CallSession(
        patient_id=call_session.patient_id,
        start_time=datetime.utcnow()
    )
    db.add(db_call_session)
    db.commit()
    db.refresh(db_call_session)
    return db_call_session


def update_call_session(db: Session, call_id: int, call_session: CallSessionUpdate) -> Optional[CallSession]:
    db_call_session = db.query(CallSession).filter(CallSession.call_id == call_id).first()
    if db_call_session:
        update_data = call_session.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_call_session, field, value)
        db.commit()
        db.refresh(db_call_session)
    return db_call_session


def end_call_session(db: Session, call_id: int) -> Optional[CallSession]:
    """End a call session by setting the end_time"""
    db_call_session = db.query(CallSession).filter(CallSession.call_id == call_id).first()
    if db_call_session:
        db_call_session.end_time = datetime.utcnow()
        db.commit()
        db.refresh(db_call_session)
    return db_call_session


def delete_call_session(db: Session, call_id: int) -> bool:
    db_call_session = db.query(CallSession).filter(CallSession.call_id == call_id).first()
    if db_call_session:
        db.delete(db_call_session)
        db.commit()
        return True
    return False 