from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.triage_assessment import TriageAssessment
from app.schemas.triage_assessment import TriageAssessmentCreate, TriageAssessmentUpdate


def get_triage_assessment(db: Session, assessment_id: int) -> Optional[TriageAssessment]:
    return db.query(TriageAssessment).filter(
        TriageAssessment.assessment_id == assessment_id
    ).first()


def get_triage_assessments(db: Session, skip: int = 0, limit: int = 100) -> List[TriageAssessment]:
    return db.query(TriageAssessment).offset(skip).limit(limit).all()


def get_triage_assessments_by_diagnosis(db: Session, diagnosis_id: int, skip: int = 0, limit: int = 100) -> List[TriageAssessment]:
    return db.query(TriageAssessment).filter(
        TriageAssessment.diagnosis_id == diagnosis_id
    ).offset(skip).limit(limit).all()


def get_triage_assessments_by_care_level(db: Session, care_level_id: int, skip: int = 0, limit: int = 100) -> List[TriageAssessment]:
    return db.query(TriageAssessment).filter(
        TriageAssessment.care_level_id == care_level_id
    ).offset(skip).limit(limit).all()


def get_triage_assessments_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[TriageAssessment]:
    return db.query(TriageAssessment).filter(
        TriageAssessment.assigned_by == user_id
    ).offset(skip).limit(limit).all()


def create_triage_assessment(db: Session, triage_assessment: TriageAssessmentCreate) -> TriageAssessment:
    db_triage_assessment = TriageAssessment(
        **triage_assessment.dict(),
        updated_at=datetime.utcnow()
    )
    db.add(db_triage_assessment)
    db.commit()
    db.refresh(db_triage_assessment)
    return db_triage_assessment


def update_triage_assessment(db: Session, assessment_id: int, triage_assessment: TriageAssessmentUpdate) -> Optional[TriageAssessment]:
    db_triage_assessment = db.query(TriageAssessment).filter(
        TriageAssessment.assessment_id == assessment_id
    ).first()
    if db_triage_assessment:
        update_data = triage_assessment.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_triage_assessment, field, value)
        db_triage_assessment.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_triage_assessment)
    return db_triage_assessment


def delete_triage_assessment(db: Session, assessment_id: int) -> bool:
    db_triage_assessment = db.query(TriageAssessment).filter(
        TriageAssessment.assessment_id == assessment_id
    ).first()
    if db_triage_assessment:
        db.delete(db_triage_assessment)
        db.commit()
        return True
    return False


def get_latest_triage_assessment(db: Session, diagnosis_id: int) -> Optional[TriageAssessment]:
    """Get the most recent triage assessment for a diagnosis"""
    return db.query(TriageAssessment).filter(
        TriageAssessment.diagnosis_id == diagnosis_id
    ).order_by(TriageAssessment.updated_at.desc()).first() 