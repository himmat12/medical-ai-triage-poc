from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class ChatHistoryBase(BaseModel):
    call_id: int
    speaker: str
    message_text: str
    message_sequence: int


class ChatHistoryCreate(BaseModel):
    call_id: int
    speaker: str
    message_text: str


class ChatHistoryUpdate(BaseModel):
    speaker: Optional[str] = None
    message_text: Optional[str] = None


class ChatHistoryInDBBase(ChatHistoryBase):
    chat_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ChatHistory(ChatHistoryInDBBase):
    pass 