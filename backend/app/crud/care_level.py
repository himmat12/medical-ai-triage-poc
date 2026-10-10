from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.care_level import CareLevel
from app.schemas.care_level import CareLevelCreate, CareLevelUpdate


def get_care_level(db: Session, level_id: int) -> Optional[CareLevel]:
    return db.query(CareLevel).filter(CareLevel.level_id == level_id).first()


def get_care_level_by_code(db: Session, level_code: str) -> Optional[CareLevel]:
    return db.query(CareLevel).filter(CareLevel.level_code == level_code).first()


def get_care_levels(db: Session, skip: int = 0, limit: int = 100, active_only: bool = False) -> List[CareLevel]:
    query = db.query(CareLevel)
    if active_only:
        query = query.filter(CareLevel.is_active == True)
    return query.offset(skip).limit(limit).all()


def create_care_level(db: Session, care_level: CareLevelCreate) -> CareLevel:
    db_care_level = CareLevel(**care_level.dict())
    db.add(db_care_level)
    db.commit()
    db.refresh(db_care_level)
    return db_care_level


def update_care_level(db: Session, level_id: int, care_level: CareLevelUpdate) -> Optional[CareLevel]:
    db_care_level = db.query(CareLevel).filter(CareLevel.level_id == level_id).first()
    if db_care_level:
        update_data = care_level.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_care_level, field, value)
        db.commit()
        db.refresh(db_care_level)
    return db_care_level


def delete_care_level(db: Session, level_id: int) -> bool:
    db_care_level = db.query(CareLevel).filter(CareLevel.level_id == level_id).first()
    if db_care_level:
        db.delete(db_care_level)
        db.commit()
        return True
    return False 