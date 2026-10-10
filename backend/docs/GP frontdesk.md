**GP Frontdesk FastAPI Project Setup Plan**

**Identified Tables**
From the ERD, the application has the following tables:

1. `User`
2. `Role`
3. `UserRole`
4. `Patient`
5. `CallSession`
6. `ChatHistory`
7. `CareLevel`
8. `Diagnosis`
9. `DiagnosisSession`
10. `TriageAssessment`

---

**Recommended FastAPI Project Folder Structure (Best Practices)**

```
gp_frontdesk/
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── endpoints/
│   │   │   │   ├── auth.py
│   │   │   │   ├── users.py
│   │   │   │   ├── patients.py
│   │   │   │   ├── sessions.py
│   │   │   │   ├── chats.py
│   │   │   │   ├── diagnoses.py
│   │   │   │   ├── assessments.py
│   │   │   │   └── roles.py
│   │   │   └── __init__.py
│   │   └── __init__.py
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   └── __init__.py
│   ├── crud/
│   │   ├── user.py
│   │   ├── patient.py
│   │   ├── session.py
│   │   ├── chat.py
│   │   ├── diagnosis.py
│   │   ├── assessment.py
│   │   ├── role.py
│   │   └── __init__.py
│   ├── models/
│   │   ├── user.py
│   │   ├── role.py
│   │   ├── patient.py
│   │   ├── session.py
│   │   ├── chat.py
│   │   ├── diagnosis.py
│   │   ├── assessment.py
│   │   └── __init__.py
│   ├── schemas/
│   │   ├── user.py
│   │   ├── role.py
│   │   ├── patient.py
│   │   ├── session.py
│   │   ├── chat.py
│   │   ├── diagnosis.py
│   │   ├── assessment.py
│   │   └── __init__.py
│   ├── db/
│   │   ├── base.py
│   │   ├── session.py
│   │   └── init_db.py
│   ├── main.py
│   └── __init__.py
├── alembic/ (optional for migrations)
├── .env
├── requirements.txt
└── README.md
```

---

**Feature Breakdown by Table**

1. **User, Role, UserRole**

   * Implement user registration, login (JWT), and password hashing.
   * Role-based access control via `UserRole` linking to `Role`.
   * Seed roles: admin, clinician, triage, support.

2. **Patient**

   * CRUD operations with user ownership via FK.
   * Include emergency contacts and symptoms capture.

3. **CallSession**

   * Start/end tracking per `patient_id`.
   * Time-based session grouping for chat and diagnosis.

4. **ChatHistory**

   * Store messages with speaker roles.
   * Support pagination and sequence tracking.

5. **CareLevel**

   * Lookup model for triage levels.
   * Populate standard levels like “low”, “medium”, “critical”.

6. **Diagnosis (Interview)**

   * Store patient-specific diagnosis records.
   * Can include integration with external diagnosis API (e.g., Infermedica).

7. **DiagnosisSession**

   * Link `CallSession` to selected `Diagnosis`.

8. **TriageAssessment**

   * Combines `Diagnosis`, `CareLevel`, and `assigned_by` (user).
   * Important for clinical decision logging.

9. **Authentication**

   * Use OAuth2 password flow with JWT.
   * Auth handled via `auth.py`, token creation via `security.py`.
   * Decorators for role-protected endpoints.

---

**Startup Tasks**

* [ ] Define SQLAlchemy models from all tables.
* [ ] Create Pydantic schemas for input/output validation.
* [ ] Set up SQLAlchemy session and DB init.
* [ ] Configure JWT authentication.
* [ ] Write CRUD logic for all entities.
* [ ] Build routers for each domain (`users`, `patients`, etc.).
* [ ] Add role-based permission checks in endpoints.
* [ ] Seed base roles and superuser.
* [ ] Write OpenAPI docs and test via Swagger UI.
* [ ] Configure `.env` for secrets/db URIs.

---

Assumptions

1. Role-based access is enforced through `UserRole`, and endpoints check this dynamically.
2. `Diagnosis.report` may depend on external API integration, assumed optional or mocked initially.
3. Chat sessions are bounded within `CallSession`; out-of-session chat is not allowed.

Confidence rating: 8/10
