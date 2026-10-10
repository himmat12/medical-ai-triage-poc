from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base


class TriageAssessment(Base):
    __tablename__ = "triage_assessments"

    assessment_id = Column(Integer, primary_key=True, index=True)
    diagnosis_id = Column(Integer, ForeignKey("diagnoses.diagnosis_id"), nullable=False)
    care_level_id = Column(Integer, ForeignKey("care_levels.level_id"), nullable=False)
    assigned_by = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    diagnosis = relationship("Diagnosis", back_populates="triage_assessments")
    care_level = relationship("CareLevel", back_populates="triage_assessments")
    assigned_by_user = relationship("User", back_populates="triage_assessments") 