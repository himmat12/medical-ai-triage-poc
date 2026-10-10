from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base


class CareLevel(Base):
    __tablename__ = "care_levels"

    level_id = Column(Integer, primary_key=True, index=True)
    level_name = Column(String(100), nullable=False)
    level_code = Column(String(20), unique=True, nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    triage_assessments = relationship("TriageAssessment", back_populates="care_level") 