# Learnova Backend - FastAPI + SQLite

## Run backend
```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open API docs:
- http://127.0.0.1:8000/docs

Default demo user is created on first run:
- Email: student@learnova.lk
- Password: password123

## Main modules
- Authentication and profile management
- Course management
- Task and assignment management
- Study planner and schedule
- Progress and performance tracking
- Notifications and settings
- Feedback and help support
