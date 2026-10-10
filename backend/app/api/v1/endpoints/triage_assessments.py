from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user
from app.crud import triage_assessment as crud_triage_assessment
from app.models.user import User
from app.schemas.triage_assessment import TriageAssessment, TriageAssessmentCreate, TriageAssessmentUpdate

router = APIRouter()


@router.get("/", response_model=List[TriageAssessment])
def read_triage_assessments(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve triage assessments
    """
    triage_assessments = crud_triage_assessment.get_triage_assessments(db, skip=skip, limit=limit)
    return triage_assessments


@router.post("/", response_model=TriageAssessment)
def create_triage_assessment(
    *,
    db: Session = Depends(get_db),
    triage_assessment_in: TriageAssessmentCreate,
    current_user: User = Depends(get_current_user),
):
    """
    Create new triage assessment
    """
    triage_assessment = crud_triage_assessment.create_triage_assessment(db, triage_assessment_in)
    return triage_assessment


@router.get("/{assessment_id}", response_model=TriageAssessment)
def read_triage_assessment(
    *,
    db: Session = Depends(get_db),
    assessment_id: int,
    current_user: User = Depends(get_current_user),
):
    """
    Get triage assessment by ID
    """
    triage_assessment = crud_triage_assessment.get_triage_assessment(db, assessment_id)
    if not triage_assessment:
        raise HTTPException(status_code=404, detail="Triage assessment not found")
    return triage_assessment


@router.put("/{assessment_id}", response_model=TriageAssessment)
def update_triage_assessment(
    *,
    db: Session = Depends(get_db),
    assessment_id: int,
    triage_assessment_in: TriageAssessmentUpdate,
    current_user: User = Depends(get_current_user),
):
    """
    Update triage assessment
    """
    triage_assessment = crud_triage_assessment.update_triage_assessment(
        db, assessment_id, triage_assessment_in
    )
    if not triage_assessment:
        raise HTTPException(status_code=404, detail="Triage assessment not found")
    return triage_assessment


@router.get("/diagnosis/{diagnosis_id}", response_model=List[TriageAssessment])
def read_triage_assessments_by_diagnosis(
    *,
    db: Session = Depends(get_db),
    diagnosis_id: int,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
):
    """
    Get triage assessments for a specific diagnosis
    """
    triage_assessments = crud_triage_assessment.get_triage_assessments_by_diagnosis(
        db, diagnosis_id, skip=skip, limit=limit
    )
    return triage_assessments


@router.get("/diagnosis/{diagnosis_id}/latest", response_model=TriageAssessment)
def read_latest_triage_assessment(
    *,
    db: Session = Depends(get_db),
    diagnosis_id: int,
    current_user: User = Depends(get_current_user),
):
    """
    Get the latest triage assessment for a diagnosis
    """
    triage_assessment = crud_triage_assessment.get_latest_triage_assessment(db, diagnosis_id)
    if not triage_assessment:
        raise HTTPException(status_code=404, detail="No triage assessment found for this diagnosis")
    return triage_assessment


@router.get("/care-level/{care_level_id}", response_model=List[TriageAssessment])
def read_triage_assessments_by_care_level(
    *,
    db: Session = Depends(get_db),
    care_level_id: int,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
):
    """
    Get triage assessments for a specific care level
    """
    triage_assessments = crud_triage_assessment.get_triage_assessments_by_care_level(
        db, care_level_id, skip=skip, limit=limit
    )
    return triage_assessments


@router.get("/user/{user_id}", response_model=List[TriageAssessment])
def read_triage_assessments_by_user(
    *,
    db: Session = Depends(get_db),
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
):
    """
    Get triage assessments assigned by a specific user
    """
    triage_assessments = crud_triage_assessment.get_triage_assessments_by_user(
        db, user_id, skip=skip, limit=limit
    )
    return triage_assessments


@router.delete("/{assessment_id}")
def delete_triage_assessment(
    *,
    db: Session = Depends(get_db),
    assessment_id: int,
    current_user: User = Depends(get_current_user),
):
    """
    Delete triage assessment
    """
    deleted = crud_triage_assessment.delete_triage_assessment(db, assessment_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Triage assessment not found")
    return {"message": "Triage assessment deleted successfully"} 