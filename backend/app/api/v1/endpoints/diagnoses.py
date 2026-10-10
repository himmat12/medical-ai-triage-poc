from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user
from app.crud import diagnosis as crud_diagnosis
from app.models.user import User
from app.schemas.diagnosis import Diagnosis, DiagnosisCreate, DiagnosisUpdate

router = APIRouter()


@router.get("/", response_model=List[Diagnosis])
def read_diagnoses(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve diagnoses
    """
    diagnoses = crud_diagnosis.get_diagnoses(db, skip=skip, limit=limit)
    return diagnoses


@router.post("/", response_model=Diagnosis)
def create_diagnosis(
    *,
    db: Session = Depends(get_db),
    diagnosis_in: DiagnosisCreate,
    current_user: User = Depends(get_current_user),
):
    """
    Create new diagnosis
    """
    diagnosis = crud_diagnosis.create_diagnosis(db, diagnosis_in)
    return diagnosis


@router.get("/{diagnosis_id}", response_model=Diagnosis)
def read_diagnosis(
    *,
    db: Session = Depends(get_db),
    diagnosis_id: int,
    current_user: User = Depends(get_current_user),
):
    """
    Get diagnosis by ID
    """
    diagnosis = crud_diagnosis.get_diagnosis(db, diagnosis_id)
    if not diagnosis:
        raise HTTPException(status_code=404, detail="Diagnosis not found")
    return diagnosis


@router.put("/{diagnosis_id}", response_model=Diagnosis)
def update_diagnosis(
    *,
    db: Session = Depends(get_db),
    diagnosis_id: int,
    diagnosis_in: DiagnosisUpdate,
    current_user: User = Depends(get_current_user),
):
    """
    Update diagnosis
    """
    diagnosis = crud_diagnosis.update_diagnosis(db, diagnosis_id, diagnosis_in)
    if not diagnosis:
        raise HTTPException(status_code=404, detail="Diagnosis not found")
    return diagnosis


@router.get("/patient/{patient_id}", response_model=List[Diagnosis])
def read_diagnoses_by_patient(
    *,
    db: Session = Depends(get_db),
    patient_id: int,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
):
    """
    Get diagnoses for a specific patient
    """
    diagnoses = crud_diagnosis.get_diagnoses_by_patient(db, patient_id, skip=skip, limit=limit)
    return diagnoses


@router.get("/search/", response_model=List[Diagnosis])
def search_diagnoses(
    *,
    db: Session = Depends(get_db),
    title: str = Query(..., description="Search term for diagnosis title"),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
):
    """
    Search diagnoses by title
    """
    diagnoses = crud_diagnosis.search_diagnoses_by_title(db, title, skip=skip, limit=limit)
    return diagnoses


@router.delete("/{diagnosis_id}")
def delete_diagnosis(
    *,
    db: Session = Depends(get_db),
    diagnosis_id: int,
    current_user: User = Depends(get_current_user),
):
    """
    Delete diagnosis
    """
    deleted = crud_diagnosis.delete_diagnosis(db, diagnosis_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Diagnosis not found")
    return {"message": "Diagnosis deleted successfully"} 