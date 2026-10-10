from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base


class DiagnosisSession(Base):
    __tablename__ = "diagnosis_sessions"

    diagnosis_session_id = Column(Integer, primary_key=True, index=True)
    call_id = Column(Integer, ForeignKey("call_sessions.call_id"), nullable=False)
    diagnosis_id = Column(Integer, ForeignKey("diagnoses.diagnosis_id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    call_session = relationship("CallSession", back_populates="diagnosis_sessions")
    diagnosis = relationship("Diagnosis", back_populates="diagnosis_sessions") 