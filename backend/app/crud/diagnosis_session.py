from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.diagnosis_session import DiagnosisSession
from app.schemas.diagnosis_session import DiagnosisSessionCreate, DiagnosisSessionUpdate


def get_diagnosis_session(db: Session, diagnosis_session_id: int) -> Optional[DiagnosisSession]:
    return db.query(DiagnosisSession).filter(
        DiagnosisSession.diagnosis_session_id == diagnosis_session_id
    ).first()


def get_diagnosis_sessions(db: Session, skip: int = 0, limit: int = 100) -> List[DiagnosisSession]:
    return db.query(DiagnosisSession).offset(skip).limit(limit).all()


def get_diagnosis_sessions_by_call(db: Session, call_id: int, skip: int = 0, limit: int = 100) -> List[DiagnosisSession]:
    return db.query(DiagnosisSession).filter(
        DiagnosisSession.call_id == call_id
    ).offset(skip).limit(limit).all()


def get_diagnosis_sessions_by_diagnosis(db: Session, diagnosis_id: int, skip: int = 0, limit: int = 100) -> List[DiagnosisSession]:
    return db.query(DiagnosisSession).filter(
        DiagnosisSession.diagnosis_id == diagnosis_id
    ).offset(skip).limit(limit).all()


def create_diagnosis_session(db: Session, diagnosis_session: DiagnosisSessionCreate) -> DiagnosisSession:
    db_diagnosis_session = DiagnosisSession(**diagnosis_session.dict())
    db.add(db_diagnosis_session)
    db.commit()
    db.refresh(db_diagnosis_session)
    return db_diagnosis_session


def update_diagnosis_session(db: Session, diagnosis_session_id: int, diagnosis_session: DiagnosisSessionUpdate) -> Optional[DiagnosisSession]:
    db_diagnosis_session = db.query(DiagnosisSession).filter(
        DiagnosisSession.diagnosis_session_id == diagnosis_session_id
    ).first()
    if db_diagnosis_session:
        update_data = diagnosis_session.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_diagnosis_session, field, value)
        db.commit()
        db.refresh(db_diagnosis_session)
    return db_diagnosis_session


def delete_diagnosis_session(db: Session, diagnosis_session_id: int) -> bool:
    db_diagnosis_session = db.query(DiagnosisSession).filter(
        DiagnosisSession.diagnosis_session_id == diagnosis_session_id
    ).first()
    if db_diagnosis_session:
        db.delete(db_diagnosis_session)
        db.commit()
        return True
    return False


def get_diagnosis_session_by_call_and_diagnosis(db: Session, call_id: int, diagnosis_id: int) -> Optional[DiagnosisSession]:
    """Get a specific diagnosis session by call_id and diagnosis_id"""
    return db.query(DiagnosisSession).filter(
        DiagnosisSession.call_id == call_id,
        DiagnosisSession.diagnosis_id == diagnosis_id
    ).first() 