from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.patient import Patient
from app.models.role import Role
from app.models.user import User
from app.models.user_role import UserRole
from app.schemas.patient import PatientCreate, PatientUpdate, PatientSignup
from app.schemas.user import UserCreate
from app.core.security import get_password_hash


def get_patient(db: Session, patient_id: int) -> Optional[Patient]:
    return db.query(Patient).filter(Patient.patient_id == patient_id).first()


def get_patients(db: Session, skip: int = 0, limit: int = 100) -> List[Patient]:
    return db.query(Patient).offset(skip).limit(limit).all()


def get_patients_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[Patient]:
    return db.query(Patient).filter(Patient.user_id == user_id).offset(skip).limit(limit).all()


def create_patient(db: Session, patient: PatientCreate, user_id: int) -> Patient:
    db_patient = Patient(
        **patient.dict(),
        user_id=user_id
    )
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    
    # Assign patient role to the user if they don't have it
    patient_role = db.query(Role).filter(Role.name == "patient").first()
    if patient_role:
        # Check if user already has patient role
        existing_role = db.query(UserRole).filter(
            UserRole.user_id == user_id,
            UserRole.role_id == patient_role.role_id
        ).first()
        
        if not existing_role:
            user_role = UserRole(user_id=user_id, role_id=patient_role.role_id)
            db.add(user_role)
            db.commit()
    
    return db_patient


def signup_patient(db: Session, patient_signup: PatientSignup) -> Patient:
    """
    Complete patient signup: creates both User and Patient records
    """
    # Check if user already exists
    existing_user_email = db.query(User).filter(User.email == patient_signup.email).first()
    if existing_user_email:
        raise ValueError("Email already registered")
    
    existing_user_username = db.query(User).filter(User.username == patient_signup.username).first()
    if existing_user_username:
        raise ValueError("Username already registered")
    
    # Create user account
    hashed_password = get_password_hash(patient_signup.password)
    db_user = User(
        username=patient_signup.username,
        email=patient_signup.email,
        password=hashed_password,
        is_active=True,
        is_complete=True,  # Patient completes profile during signup
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Assign patient role
    patient_role = db.query(Role).filter(Role.name == "patient").first()
    if patient_role:
        user_role = UserRole(user_id=db_user.user_id, role_id=patient_role.role_id)
        db.add(user_role)
        db.commit()
    
    # Create patient record
    patient_data = {
        "fullname": patient_signup.fullname,
        "dob": patient_signup.dob,
        "age": patient_signup.age,
        "gender": patient_signup.gender,
        "symptoms": patient_signup.symptoms,
        "conditions": patient_signup.conditions,
        "phone": patient_signup.phone,
        "address": patient_signup.address,
        "emergency_contact_name": patient_signup.emergency_contact_name,
        "emergency_contact_phone": patient_signup.emergency_contact_phone,
        "user_id": db_user.user_id,
    }
    
    db_patient = Patient(**patient_data)
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    
    return db_patient


def update_patient(db: Session, patient_id: int, patient: PatientUpdate) -> Optional[Patient]:
    db_patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if db_patient:
        update_data = patient.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_patient, field, value)
        db.commit()
        db.refresh(db_patient)
    return db_patient


def delete_patient(db: Session, patient_id: int) -> bool:
    db_patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if db_patient:
        db.delete(db_patient)
        db.commit()
        return True
    return False 