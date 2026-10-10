from typing import Optional
from pydantic import BaseModel, EmailStr
from datetime import date, datetime


class PatientBase(BaseModel):
    fullname: str
    dob: date
    age: int
    gender: str
    symptoms: Optional[str] = None
    conditions: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None


class PatientCreate(PatientBase):
    pass


class PatientSignup(BaseModel):
    """Schema for patient self-registration - combines user and patient data"""
    # User fields
    username: str
    email: EmailStr
    password: str
    
    # Patient fields
    fullname: str
    dob: date
    age: int
    gender: str
    symptoms: Optional[str] = None
    conditions: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None


class PatientUpdate(BaseModel):
    fullname: Optional[str] = None
    dob: Optional[date] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    symptoms: Optional[str] = None
    conditions: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None


class PatientInDBBase(PatientBase):
    patient_id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Patient(PatientInDBBase):
    pass


class PatientWithUser(PatientInDBBase):
    """Patient data with associated user information"""
    user: Optional[dict] = None 