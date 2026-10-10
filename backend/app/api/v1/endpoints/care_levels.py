from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user
from app.crud import care_level as crud_care_level
from app.models.user import User
from app.schemas.care_level import CareLevel, CareLevelCreate, CareLevelUpdate

router = APIRouter()


@router.get("/", response_model=List[CareLevel])
def read_care_levels(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve care levels
    """
    care_levels = crud_care_level.get_care_levels(db, skip=skip, limit=limit, active_only=active_only)
    return care_levels


@router.post("/", response_model=CareLevel)
def create_care_level(
    *,
    db: Session = Depends(get_db),
    care_level_in: CareLevelCreate,
    current_user: User = Depends(get_current_user),
):
    """
    Create new care level
    """
    # Check if care level code already exists
    if crud_care_level.get_care_level_by_code(db, care_level_in.level_code):
        raise HTTPException(
            status_code=400,
            detail="Care level with this code already exists."
        )
    
    care_level = crud_care_level.create_care_level(db, care_level_in)
    return care_level


@router.get("/{level_id}", response_model=CareLevel)
def read_care_level(
    *,
    db: Session = Depends(get_db),
    level_id: int,
    current_user: User = Depends(get_current_user),
):
    """
    Get care level by ID
    """
    care_level = crud_care_level.get_care_level(db, level_id)
    if not care_level:
        raise HTTPException(status_code=404, detail="Care level not found")
    return care_level


@router.put("/{level_id}", response_model=CareLevel)
def update_care_level(
    *,
    db: Session = Depends(get_db),
    level_id: int,
    care_level_in: CareLevelUpdate,
    current_user: User = Depends(get_current_user),
):
    """
    Update care level
    """
    care_level = crud_care_level.update_care_level(db, level_id, care_level_in)
    if not care_level:
        raise HTTPException(status_code=404, detail="Care level not found")
    return care_level


@router.delete("/{level_id}")
def delete_care_level(
    *,
    db: Session = Depends(get_db),
    level_id: int,
    current_user: User = Depends(get_current_user),
):
    """
    Delete care level
    """
    deleted = crud_care_level.delete_care_level(db, level_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Care level not found")
    return {"message": "Care level deleted successfully"} 