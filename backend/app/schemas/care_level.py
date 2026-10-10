from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class CareLevelBase(BaseModel):
    level_name: str
    level_code: str
    description: Optional[str] = None
    is_active: bool = True


class CareLevelCreate(CareLevelBase):
    pass


class CareLevelUpdate(BaseModel):
    level_name: Optional[str] = None
    level_code: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class CareLevelInDBBase(CareLevelBase):
    level_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class CareLevel(CareLevelInDBBase):
    pass 