from sqlalchemy.orm import Session
from app.core.security import get_password_hash
from app.db import base  # noqa: F401
from app.db.session import engine
from app.models import User, Role, UserRole, CareLevel


def init_db(db: Session) -> None:
    # Tables should be created with Alembic migrations
    # But if you don't want to use migrations, uncomment next line
    base.Base.metadata.create_all(bind=engine)

    # Create initial roles
    roles_data = [
        {"name": "admin"},
        {"name": "clinician"},
        {"name": "triage"},
        {"name": "support"},
        {"name": "patient"}  # Patients are also users who need to login
    ]
    
    for role_data in roles_data:
        role = db.query(Role).filter(Role.name == role_data["name"]).first()
        if not role:
            role = Role(**role_data)
            db.add(role)
    
    # Create initial care levels
    care_levels_data = [
        {"level_name": "Low Priority", "level_code": "LOW", "description": "Non-urgent care"},
        {"level_name": "Medium Priority", "level_code": "MED", "description": "Standard care needed"},
        {"level_name": "High Priority", "level_code": "HIGH", "description": "Urgent care required"},
        {"level_name": "Critical", "level_code": "CRIT", "description": "Emergency care needed immediately"}
    ]
    
    for care_level_data in care_levels_data:
        care_level = db.query(CareLevel).filter(CareLevel.level_code == care_level_data["level_code"]).first()
        if not care_level:
            care_level = CareLevel(**care_level_data)
            db.add(care_level)
    
    # Commit roles and care levels first
    db.commit()
    
    # Create superuser
    user = db.query(User).filter(User.email == "admin@gpfrontdesk.com").first()
    if not user:
        user = User(
            username="admin",
            email="admin@gpfrontdesk.com",
            password=get_password_hash("admin123"),
            is_active=True,
            is_complete=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Assign admin role to superuser
        admin_role = db.query(Role).filter(Role.name == "admin").first()
        if admin_role:
            user_role = UserRole(user_id=user.user_id, role_id=admin_role.role_id)
            db.add(user_role)
            db.commit()
    
    # Final commit to ensure everything is saved
    db.commit() 