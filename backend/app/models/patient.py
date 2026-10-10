from sqlalchemy import Column, Integer, String, Date, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base


class Patient(Base):
    __tablename__ = "patients"

    patient_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    fullname = Column(String(255), nullable=False)
    dob = Column(Date, nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String(10), nullable=False)
    symptoms = Column(Text)
    conditions = Column(Text, comment="health conditions")
    phone = Column(String(20))
    address = Column(Text)
    emergency_contact_name = Column(String(255))
    emergency_contact_phone = Column(String(20))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="patients")
    call_sessions = relationship("CallSession", back_populates="patient")
    diagnoses = relationship("Diagnosis", back_populates="patient") 