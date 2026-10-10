from typing import Optional
from pydantic import BaseModel


class RoleBase(BaseModel):
    name: str


class RoleCreate(RoleBase):
    pass


class RoleUpdate(BaseModel):
    name: Optional[str] = None


class RoleInDBBase(RoleBase):
    role_id: int

    class Config:
        from_attributes = True


class Role(RoleInDBBase):
    pass 