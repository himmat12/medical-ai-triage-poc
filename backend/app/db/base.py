# Import all the SQLAlchemy models, so that Base has them before being
# imported by Alembic
from app.db.session import Base  # noqa
from app.models.user import User  # noqa
from app.models.role import Role  # noqa
from app.models.user_role import UserRole  # noqa
from app.models.patient import Patient  # noqa
from app.models.care_level import CareLevel  # noqa
from app.models.call_session import CallSession  # noqa
from app.models.chat_history import ChatHistory  # noqa
from app.models.diagnosis import Diagnosis  # noqa
from app.models.diagnosis_session import DiagnosisSession  # noqa
from app.models.triage_assessment import TriageAssessment  # noqa 