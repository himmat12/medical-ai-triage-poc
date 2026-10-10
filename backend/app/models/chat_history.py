from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base


class ChatHistory(Base):
    __tablename__ = "chat_history"

    chat_id = Column(Integer, primary_key=True, index=True)
    call_id = Column(Integer, ForeignKey("call_sessions.call_id"), nullable=False)
    speaker = Column(String(50), nullable=False, comment="role of speaker")
    message_text = Column(Text, nullable=False)
    message_sequence = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    call_session = relationship("CallSession", back_populates="chat_history") 