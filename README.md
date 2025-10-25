# ServiceDesk Backend

JWT Authentication service for the ServiceDesk application.

## Features
- User authentication with JWT tokens
- Refresh token support
- Password hashing with Werkzeug
- SQLAlchemy ORM integration

## Setup
1. Install dependencies: `pip install -r requirements.txt`
2. Copy `.env.example` to `.env` and configure
3. Run the application: `python app.py`

## API Endpoints
- POST `/api/auth/login` - User login
- POST `/api/auth/refresh` - Refresh access token
- GET `/api/auth/me` - Get current user
- POST `/api/auth/logout` - User logout