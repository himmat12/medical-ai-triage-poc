from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class TriageAssessmentBase(BaseModel):
    diagnosis_id: int
    care_level_id: int
    assigned_by: int


class TriageAssessmentCreate(TriageAssessmentBase):
    pass


class TriageAssessmentUpdate(BaseModel):
    diagnosis_id: Optional[int] = None
    care_level_id: Optional[int] = None
    assigned_by: Optional[int] = None


class TriageAssessmentInDBBase(TriageAssessmentBase):
    assessment_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TriageAssessment(TriageAssessmentInDBBase):
    pass 