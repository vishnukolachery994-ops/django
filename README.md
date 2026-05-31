# Django Cookie-Based Authentication API

A Django REST Framework project implementing cookie-based authentication with OTP email verification.

## Features
- User registration with OTP email verification
- Cookie-based authentication (HttpOnly, Secure flags)
- Swagger UI with automatic CSRF token generation
- Protected endpoints via custom DRF authentication class
- Frontend HTML demo included

## Setup Instructions

### 1. Clone and create virtual environment
```bash
git clone <your-repo-url>
cd django_auth_project
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Create superuser (optional)
```bash
python manage.py createsuperuser
```

### 5. Run the server
```bash
python manage.py runserver
```

## API Endpoints

| Method | URL | Description | Auth Required |
|--------|-----|-------------|---------------|
| POST | /api/register/ | Register new user | No |
| POST | /api/register/verify/ | Verify OTP | No |
| POST | /api/login/ | Login, sets cookie | No |
| GET | /api/me/ | Get user details | Yes |
| POST | /api/logout/ | Logout, clears cookie | Yes |

## Testing
- **Swagger UI**: http://localhost:8000/swagger/ (auto-sets CSRF cookie)
- **Frontend Demo**: http://localhost:8000/
- **Admin Panel**: http://localhost:8000/admin/

## OTP in Development
OTP codes print to the terminal (console email backend). Check your terminal after registering.
