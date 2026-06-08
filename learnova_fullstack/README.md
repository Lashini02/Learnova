# Learnova Full-Stack Project

Learnova is a Student Learning & Task Organizer app. This full-stack version includes:

## Frontend
- Flutter + Dart mobile app
- Creative pastel UI
- Splash, Login, Sign Up, Forgot Password, Dashboard
- Profile Management
- Course Management
- Task & Assignment Management
- Study Planner & Schedule
- Progress & Performance Tracking
- Notifications & Settings
- Feedback and Help Support
- API service file ready for backend connection

## Backend
- FastAPI REST API
- SQLite database
- JWT authentication
- CRUD APIs for courses, tasks, study sessions, progress, goals, settings and feedback
- Demo seed data

## Requirements covered from assignment brief
- Common screens: Splash, Login, Home/Dashboard
- Member 1: Authentication & Profile Management
- Member 2: Course Management
- Member 3: Task & Assignment Management
- Member 4: Study Planner & Schedule
- Member 5: Progress & Performance Tracking
- Member 6: Notifications & Settings

## How to run backend
```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend docs:
```text
http://127.0.0.1:8000/docs
```

Demo login:
```text
Email: student@learnova.lk
Password: password123
```

## How to run frontend
```bash
cd frontend
flutter pub get
flutter run
```

Important API URL:
- Android emulator: `http://10.0.2.2:8000/api`
- Browser/Desktop: `http://127.0.0.1:8000/api`
- Real phone: use your laptop IP, example `http://192.168.1.5:8000/api`

Change it here:
```text
frontend/lib/services/api_service.dart
```

## Suggested assignment explanation
This system helps students organize learning activities by managing courses, assignments, study schedules, progress, notifications and profile details in one mobile application. The Flutter frontend provides a friendly and creative UI, while the FastAPI backend stores and manages student data using SQLite.

## Member 1 Authentication Update

This version includes the real-world style authentication improvements requested for Member 1:

- Login with email or student ID.
- JWT token saved using SharedPreferences.
- Splash screen checks saved login session and opens Dashboard automatically.
- Profile screen loads authenticated user data from backend.
- Edit Profile saves name, email, student ID, and course to backend database.
- Forgot Password demo flow includes password reset.
- Change Password screen and backend endpoint.
- Logout clears saved token and returns to Login.

Demo login:

- Email: student@learnova.lk
- Student ID: LEA-2026-001
- Password: password123

## Member 2 Course Management Update

The Course Management module now includes real backend-connected CRUD functionality, search, progress tracking, archive/restore, permanent delete confirmation, and validation. See `MEMBER2_COURSE_UPDATE_NOTES.md` for details.
