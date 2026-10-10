from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base


class Diagnosis(Base):
    __tablename__ = "diagnoses"

    diagnosis_id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.patient_id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    report = Column(Text, comment="detailed diagnosis report from inframedica API")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    patient = relationship("Patient", back_populates="diagnoses")
    diagnosis_sessions = relationship("DiagnosisSession", back_populates="diagnosis")
    triage_assessments = relationship("TriageAssessment", back_populates="diagnosis") 