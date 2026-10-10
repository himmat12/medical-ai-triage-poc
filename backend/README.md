# GP Frontdesk API

A comprehensive FastAPI application for General Practice Frontdesk Management System with complete authentication and role-based access control.

## Features

- **Complete Authentication System**: JWT-based authentication with role-based access control
- **User Management**: Full CRUD operations for users with role assignments
- **Patient Management**: Complete patient records management
- **Database Models**: All 10 tables from the ERD implemented
- **Role-Based Access Control**: Admin, Clinician, Triage, and Support roles
- **SQLite Database**: Lightweight database for development
- **Auto-generated Documentation**: Swagger UI and ReDoc

## Database Schema

The application implements all tables from the ERD:

1. **User** - System users with authentication
2. **Role** - User roles (admin, clinician, triage, support)
3. **UserRole** - Many-to-many relationship between users and roles
4. **Patient** - Patient records with demographics and medical info
5. **CallSession** - Patient call sessions
6. **ChatHistory** - Chat messages during sessions
7. **CareLevel** - Triage care levels (Low, Medium, High, Critical)
8. **Diagnosis** - Diagnosis records from interviews
9. **DiagnosisSession** - Links diagnoses to call sessions
10. **TriageAssessment** - Triage assessments linking diagnoses to care levels

## Quick Start

### Prerequisites

- Python 3.8+
- pip

### Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the root directory:
```env
DATABASE_URL=sqlite:///./gp_frontdesk.db
SECRET_KEY=your-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Running the Application

```bash
# Start the development server
uvicorn app.main:app --reload

# Or run directly
python app/main.py
```

The API will be available at:
- **API Base URL**: http://localhost:8000
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Default Credentials

A default admin user is created on first startup:
- **Username**: admin
- **Password**: admin123
- **Email**: admin@gpfrontdesk.com

## API Endpoints

### Authentication
- `POST /api/v1/auth/login` - Login with form data
- `POST /api/v1/auth/login/json` - Login with JSON data
- `POST /api/v1/auth/register` - Register new user
- `GET /api/v1/auth/me` - Get current user info

### Users
- `GET /api/v1/users/` - List all users (admin only)
- `GET /api/v1/users/{user_id}` - Get user by ID
- `POST /api/v1/users/` - Create new user (admin only)
- `PUT /api/v1/users/{user_id}` - Update user
- `DELETE /api/v1/users/{user_id}` - Delete user (admin only)
- `POST /api/v1/users/{user_id}/roles/{role_name}` - Assign role (admin only)
- `GET /api/v1/users/{user_id}/roles` - Get user roles

### Patients
- `GET /api/v1/patients/` - List patients (filtered by role)
- `GET /api/v1/patients/{patient_id}` - Get patient by ID
- `POST /api/v1/patients/` - Create new patient
- `PUT /api/v1/patients/{patient_id}` - Update patient
- `DELETE /api/v1/patients/{patient_id}` - Delete patient
- `GET /api/v1/patients/user/{user_id}` - Get patients by user

## Authentication

The API uses JWT Bearer token authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

## Roles and Permissions

### Admin
- Full access to all endpoints
- Can manage users and assign roles
- Can view and manage all patients

### Clinician
- Can view and manage all patients
- Cannot manage users or roles

### Triage
- Can access triage-related endpoints
- Limited patient access

### Support
- Basic support access
- Limited permissions

## Project Structure

```
app/
├── api/
│   └── v1/
│       ├── endpoints/
│       │   ├── auth.py          # Authentication endpoints
│       │   ├── users.py         # User management endpoints
│       │   └── patients.py      # Patient management endpoints
│       └── api.py               # API router
├── core/
│   ├── config.py                # Configuration settings
│   ├── security.py              # Security utilities
│   └── deps.py                  # Dependencies and auth
├── crud/
│   ├── user.py                  # User CRUD operations
│   └── patient.py               # Patient CRUD operations
├── db/
│   ├── base.py                  # Database base imports
│   ├── session.py               # Database session
│   └── init_db.py               # Database initialization
├── models/
│   ├── user.py                  # User SQLAlchemy model
│   ├── role.py                  # Role SQLAlchemy model
│   ├── patient.py               # Patient SQLAlchemy model
│   └── ...                      # Other models
├── schemas/
│   ├── user.py                  # User Pydantic schemas
│   ├── patient.py               # Patient Pydantic schemas
│   └── ...                      # Other schemas
└── main.py                      # FastAPI application
```

## Development

### Adding New Endpoints

1. Create CRUD operations in `app/crud/`
2. Create Pydantic schemas in `app/schemas/`
3. Create API endpoints in `app/api/v1/endpoints/`
4. Add router to `app/api/v1/api.py`

### Database Changes

The application automatically creates tables on startup. For production, consider using Alembic migrations.

## Security Features

- Password hashing with bcrypt
- JWT token authentication
- Role-based access control
- Input validation with Pydantic
- CORS middleware configured

## Testing

Use the Swagger UI at http://localhost:8000/docs to test the API endpoints interactively.

## Production Considerations

1. Change the `SECRET_KEY` in production
2. Configure specific CORS origins
3. Use a production database (PostgreSQL, MySQL)
4. Set up proper logging
5. Use environment variables for configuration
6. Add rate limiting
7. Set up monitoring and health checks

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License. 