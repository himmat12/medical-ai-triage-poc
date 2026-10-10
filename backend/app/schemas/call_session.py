from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class CallSessionBase(BaseModel):
    patient_id: int
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class CallSessionCreate(BaseModel):
    patient_id: int


class CallSessionUpdate(BaseModel):
    end_time: Optional[datetime] = None


class CallSessionInDBBase(CallSessionBase):
    call_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class CallSession(CallSessionInDBBase):
    pass 