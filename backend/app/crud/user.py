from typing import Optional, List
from sqlalchemy.orm import Session
from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.models.role import Role
from app.models.user_role import UserRole
from app.schemas.user import UserCreate, UserUpdate


def get_user(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.user_id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()


def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    return db.query(User).offset(skip).limit(limit).all()


def create_user(db: Session, user: UserCreate) -> User:
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        password=hashed_password,
        is_active=user.is_active,
        is_complete=user.is_complete,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def create_user_with_role(db: Session, user: UserCreate, role_name: str) -> User:
    """Create a user and assign a specific role"""
    # Create the user first
    db_user = create_user(db, user)
    
    # Assign the role
    success = assign_role_to_user(db, db_user.user_id, role_name)
    if not success:
        # If role assignment fails, we might want to handle this differently
        # For now, we'll just return the user without the role
        pass
    
    return db_user


def update_user(db: Session, user_id: int, user: UserUpdate) -> Optional[User]:
    db_user = db.query(User).filter(User.user_id == user_id).first()
    if db_user:
        update_data = user.dict(exclude_unset=True)
        if "password" in update_data:
            update_data["password"] = get_password_hash(update_data["password"])
        for field, value in update_data.items():
            setattr(db_user, field, value)
        db.commit()
        db.refresh(db_user)
    return db_user


def delete_user(db: Session, user_id: int) -> bool:
    db_user = db.query(User).filter(User.user_id == user_id).first()
    if db_user:
        db.delete(db_user)
        db.commit()
        return True
    return False


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.password):
        return None
    return user


def get_user_roles(db: Session, user_id: int) -> List[str]:
    user_roles = db.query(UserRole).filter(UserRole.user_id == user_id).all()
    role_ids = [ur.role_id for ur in user_roles]
    roles = db.query(Role).filter(Role.role_id.in_(role_ids)).all()
    return [role.name for role in roles]


def assign_role_to_user(db: Session, user_id: int, role_name: str) -> bool:
    role = db.query(Role).filter(Role.name == role_name).first()
    if not role:
        return False
    
    existing = db.query(UserRole).filter(
        UserRole.user_id == user_id, 
        UserRole.role_id == role.role_id
    ).first()
    if existing:
        return True
    
    user_role = UserRole(user_id=user_id, role_id=role.role_id)
    db.add(user_role)
    db.commit()
    return True


def remove_role_from_user(db: Session, user_id: int, role_name: str) -> bool:
    """Remove a role from a user"""
    role = db.query(Role).filter(Role.name == role_name).first()
    if not role:
        return False
    
    user_role = db.query(UserRole).filter(
        UserRole.user_id == user_id,
        UserRole.role_id == role.role_id
    ).first()
    
    if user_role:
        db.delete(user_role)
        db.commit()
        return True
    return False 