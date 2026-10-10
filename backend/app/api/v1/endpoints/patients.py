from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.deps import get_current_active_user
from app.crud.patient import (
    get_patient,
    get_patients,
    get_patients_by_user,
    create_patient,
    update_patient,
    delete_patient
)
from app.crud.user import get_user_roles
from app.db.session import get_db
from app.schemas.patient import Patient, PatientCreate, PatientUpdate
from app.models.user import User

router = APIRouter()


@router.get("/", response_model=List[Patient])
def read_patients(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    user_roles = get_user_roles(db, current_user.user_id)
    
    # Admins and clinicians can see all patients
    if any(role in user_roles for role in ["admin", "clinician"]):
        patients = get_patients(db, skip=skip, limit=limit)
    # Patients can only see their own patient records
    elif "patient" in user_roles:
        patients = get_patients_by_user(db, user_id=current_user.user_id, skip=skip, limit=limit)
    else:
        # Other roles (triage, support) can only see their own patients if any
        patients = get_patients_by_user(db, user_id=current_user.user_id, skip=skip, limit=limit)
    
    return patients


@router.get("/{patient_id}", response_model=Patient)
def read_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    db_patient = get_patient(db, patient_id=patient_id)
    if db_patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    user_roles = get_user_roles(db, current_user.user_id)
    
    # Check permissions: admin/clinician can access all, patients can access their own
    if not (db_patient.user_id == current_user.user_id or 
            any(role in user_roles for role in ["admin", "clinician"])):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return db_patient


@router.post("/", response_model=Patient)
def create_new_patient(
    patient: PatientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    user_roles = get_user_roles(db, current_user.user_id)
    
    # Admin, clinician, and patients can create patient records
    # (patients create their own records, staff create for others)
    if not any(role in user_roles for role in ["admin", "clinician", "patient"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to create patient records"
        )
    
    return create_patient(db=db, patient=patient, user_id=current_user.user_id)


@router.put("/{patient_id}", response_model=Patient)
def update_existing_patient(
    patient_id: int,
    patient: PatientUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    db_patient = get_patient(db, patient_id=patient_id)
    if db_patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    user_roles = get_user_roles(db, current_user.user_id)
    
    # Check permissions: admin/clinician can update all, patients can update their own
    if not (db_patient.user_id == current_user.user_id or 
            any(role in user_roles for role in ["admin", "clinician"])):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    db_patient = update_patient(db=db, patient_id=patient_id, patient=patient)
    return db_patient


@router.delete("/{patient_id}")
def delete_existing_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    db_patient = get_patient(db, patient_id=patient_id)
    if db_patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    user_roles = get_user_roles(db, current_user.user_id)
    
    # Only admin and clinician can delete patient records
    # Patients should not be able to delete their own records for audit purposes
    if not any(role in user_roles for role in ["admin", "clinician"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    success = delete_patient(db=db, patient_id=patient_id)
    if not success:
        raise HTTPException(status_code=404, detail="Patient not found")
    return {"message": "Patient deleted successfully"}


@router.get("/user/{user_id}", response_model=List[Patient])
def read_patients_by_user(
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    user_roles = get_user_roles(db, current_user.user_id)
    
    # Check permissions: admin/clinician can access all, patients can access their own
    if not (user_id == current_user.user_id or 
            any(role in user_roles for role in ["admin", "clinician"])):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return get_patients_by_user(db, user_id=user_id, skip=skip, limit=limit) 