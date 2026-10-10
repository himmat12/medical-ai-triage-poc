from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.deps import get_current_active_user, require_admin
from app.crud.user import (
    get_user,
    get_users,
    create_user,
    update_user,
    delete_user,
    assign_role_to_user,
    get_user_roles
)
from app.db.session import get_db
from app.schemas.user import User, UserCreate, UserUpdate
from app.models.user import User as UserModel

router = APIRouter()


@router.get("/", response_model=List[User])
def read_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_admin)
):
    users = get_users(db, skip=skip, limit=limit)
    return users


@router.get("/{user_id}", response_model=User)
def read_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    # Users can only read their own data unless they're admin
    if current_user.user_id != user_id:
        # Check if user has admin role
        user_roles = get_user_roles(db, current_user.user_id)
        if "admin" not in user_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
    
    db_user = get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@router.post("/", response_model=User)
def create_new_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_admin)
):
    return create_user(db=db, user=user)


@router.put("/{user_id}", response_model=User)
def update_existing_user(
    user_id: int,
    user: UserUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    # Users can only update their own data unless they're admin
    if current_user.user_id != user_id:
        user_roles = get_user_roles(db, current_user.user_id)
        if "admin" not in user_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
    
    db_user = update_user(db=db, user_id=user_id, user=user)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@router.delete("/{user_id}")
def delete_existing_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_admin)
):
    success = delete_user(db=db, user_id=user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}


@router.post("/{user_id}/roles/{role_name}")
def assign_role(
    user_id: int,
    role_name: str,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_admin)
):
    success = assign_role_to_user(db=db, user_id=user_id, role_name=role_name)
    if not success:
        raise HTTPException(status_code=400, detail="Could not assign role")
    return {"message": f"Role {role_name} assigned successfully"}


@router.get("/{user_id}/roles", response_model=List[str])
def get_user_role_list(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    # Users can only read their own roles unless they're admin
    if current_user.user_id != user_id:
        user_roles = get_user_roles(db, current_user.user_id)
        if "admin" not in user_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
    
    return get_user_roles(db, user_id) 