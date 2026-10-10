from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.diagnosis import Diagnosis
from app.schemas.diagnosis import DiagnosisCreate, DiagnosisUpdate


def get_diagnosis(db: Session, diagnosis_id: int) -> Optional[Diagnosis]:
    return db.query(Diagnosis).filter(Diagnosis.diagnosis_id == diagnosis_id).first()


def get_diagnoses(db: Session, skip: int = 0, limit: int = 100) -> List[Diagnosis]:
    return db.query(Diagnosis).offset(skip).limit(limit).all()


def get_diagnoses_by_patient(db: Session, patient_id: int, skip: int = 0, limit: int = 100) -> List[Diagnosis]:
    return db.query(Diagnosis).filter(Diagnosis.patient_id == patient_id).offset(skip).limit(limit).all()


def create_diagnosis(db: Session, diagnosis: DiagnosisCreate) -> Diagnosis:
    db_diagnosis = Diagnosis(**diagnosis.dict())
    db.add(db_diagnosis)
    db.commit()
    db.refresh(db_diagnosis)
    return db_diagnosis


def update_diagnosis(db: Session, diagnosis_id: int, diagnosis: DiagnosisUpdate) -> Optional[Diagnosis]:
    db_diagnosis = db.query(Diagnosis).filter(Diagnosis.diagnosis_id == diagnosis_id).first()
    if db_diagnosis:
        update_data = diagnosis.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_diagnosis, field, value)
        db.commit()
        db.refresh(db_diagnosis)
    return db_diagnosis


def delete_diagnosis(db: Session, diagnosis_id: int) -> bool:
    db_diagnosis = db.query(Diagnosis).filter(Diagnosis.diagnosis_id == diagnosis_id).first()
    if db_diagnosis:
        db.delete(db_diagnosis)
        db.commit()
        return True
    return False


def search_diagnoses_by_title(db: Session, title_search: str, skip: int = 0, limit: int = 100) -> List[Diagnosis]:
    """Search diagnoses by title (case-insensitive partial match)"""
    return db.query(Diagnosis).filter(
        Diagnosis.title.ilike(f"%{title_search}%")
    ).offset(skip).limit(limit).all() 