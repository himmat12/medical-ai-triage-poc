from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class DiagnosisBase(BaseModel):
    patient_id: int
    title: str
    description: Optional[str] = None
    report: Optional[str] = None


class DiagnosisCreate(DiagnosisBase):
    pass


class DiagnosisUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    report: Optional[str] = None


class DiagnosisInDBBase(DiagnosisBase):
    diagnosis_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class Diagnosis(DiagnosisInDBBase):
    pass 