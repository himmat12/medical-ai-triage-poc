from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class DiagnosisSessionBase(BaseModel):
    call_id: int
    diagnosis_id: int


class DiagnosisSessionCreate(DiagnosisSessionBase):
    pass


class DiagnosisSessionUpdate(BaseModel):
    call_id: Optional[int] = None
    diagnosis_id: Optional[int] = None


class DiagnosisSessionInDBBase(DiagnosisSessionBase):
    diagnosis_session_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class DiagnosisSession(DiagnosisSessionInDBBase):
    pass 