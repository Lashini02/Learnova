from fastapi import APIRouter, Depends, HTTPException  # type: ignore
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session  # type: ignore
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.models import User, Course, Task, StudySession, ProgressEntry, Goal, NotificationSetting, AppSetting, Feedback
from app.schemas.schemas import (
    CourseCreate, CourseRead, CourseUpdate, TaskCreate, TaskRead, TaskUpdate, TaskSummary,
    StudySessionCreate, StudySessionRead, StudySessionUpdate,
    ProgressCreate, ProgressRead, ProgressUpdate, GoalCreate, GoalRead, GoalUpdate,
    NotificationSettingsRead, NotificationSettingsUpdate, AppSettingsRead, AppSettingsUpdate,
    FeedbackCreate, FeedbackRead, FeedbackUpdate, DashboardSummary, NotificationRead
)

router = APIRouter(tags=["Learnova Modules"])

def get_owned(db: Session, model, item_id: int, user_id: int):
    item = db.query(model).filter(model.id == item_id, model.user_id == user_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

def update_model(obj, payload):
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(obj, key, value)


def _parse_date(value: str):
    if not value:
        return None
    value = value.strip()
    if value.lower() == "today":
        return date.today()
    formats = ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y"]
    for fmt in formats:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            pass
    return None

def _days_until(value: str):
    due = _parse_date(value)
    if due is None:
        return None
    return (due - date.today()).days


def _week_day_from_entry_date(entry_date: str | None) -> str:
    parsed = _parse_date(entry_date or "Today")
    target = parsed or date.today()
    return target.strftime("%a")

def _settings_for(db: Session, user_id: int):
    item = db.query(NotificationSetting).filter(NotificationSetting.user_id == user_id).first()
    if not item:
        item = NotificationSetting(user_id=user_id)
        db.add(item); db.commit(); db.refresh(item)
    return item

@router.get("/dashboard", response_model=DashboardSummary)
def dashboard(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    tasks = db.query(Task).filter(Task.user_id == current_user.id).all()
    progress_entries = db.query(ProgressEntry).filter(ProgressEntry.user_id == current_user.id).all()

    today = date.today()
    task_rows = [(task, _parse_date(task.due_date)) for task in tasks]
    pending_tasks = [task for task, _ in task_rows if not task.completed]
    today_tasks = [task for task, parsed_due in task_rows if not task.completed and parsed_due == today]
    up_next = sorted(
        pending_tasks,
        key=lambda task: (
            _parse_date(task.due_date) or date.max,
            task.id,
        ),
    )[:5]

    return DashboardSummary(
        student_name=current_user.name,
        today_tasks=len(today_tasks),
        pending_tasks=len(pending_tasks),
        completed_tasks=sum(1 for t in tasks if t.completed),
        upcoming_deadlines=len(pending_tasks),
        active_courses=db.query(Course).filter(Course.user_id == current_user.id, Course.archived == False).count(),
        study_sessions=db.query(StudySession).filter(StudySession.user_id == current_user.id).count(),
        total_study_hours=sum(p.study_hours for p in progress_entries),
        up_next=up_next,
    )

@router.get("/courses", response_model=list[CourseRead])
def list_courses(include_archived: bool = False, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = db.query(Course).filter(Course.user_id == current_user.id)
    if not include_archived:
        query = query.filter(Course.archived == False)
    return query.order_by(Course.id.desc()).all()

@router.get("/courses/archived", response_model=list[CourseRead])
def list_archived_courses(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Course).filter(Course.user_id == current_user.id, Course.archived == True).order_by(Course.id.desc()).all()

@router.get("/courses/{item_id}", response_model=CourseRead)
def get_course(item_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_owned(db, Course, item_id, current_user.id)

@router.post("/courses", response_model=CourseRead, status_code=201)
def create_course(payload: CourseCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = Course(user_id=current_user.id, **payload.model_dump())
    db.add(item); db.commit(); db.refresh(item); return item

@router.put("/courses/{item_id}", response_model=CourseRead)
def update_course(item_id: int, payload: CourseUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = get_owned(db, Course, item_id, current_user.id); update_model(item, payload); db.commit(); db.refresh(item); return item

@router.put("/courses/{item_id}/archive", response_model=CourseRead)
def archive_course(item_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = get_owned(db, Course, item_id, current_user.id)
    item.archived = True
    db.commit(); db.refresh(item); return item

@router.put("/courses/{item_id}/restore", response_model=CourseRead)
def restore_course(item_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = get_owned(db, Course, item_id, current_user.id)
    item.archived = False
    db.commit(); db.refresh(item); return item

@router.delete("/courses/{item_id}")
def delete_course(item_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = get_owned(db, Course, item_id, current_user.id); db.delete(item); db.commit(); return {"message": "Course permanently deleted"}

@router.get("/tasks", response_model=list[TaskRead])
def list_tasks(
    status: str | None = None,
    priority: str | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Task).filter(Task.user_id == current_user.id)
    if status == "pending":
        query = query.filter(Task.completed == False)
    elif status == "completed":
        query = query.filter(Task.completed == True)
    if priority in ["High", "Medium", "Low"]:
        query = query.filter(Task.priority == priority)
    if search:
        like = f"%{search.strip()}%"
        query = query.filter((Task.title.ilike(like)) | (Task.course.ilike(like)) | (Task.description.ilike(like)))
    return query.order_by(Task.completed.asc(), Task.due_date.asc(), Task.id.desc()).all()

@router.get("/tasks/summary", response_model=TaskSummary)
def task_summary(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    tasks = db.query(Task).filter(Task.user_id == current_user.id).all()
    return TaskSummary(
        total=len(tasks),
        pending=sum(1 for t in tasks if not t.completed),
        completed=sum(1 for t in tasks if t.completed),
        high_priority=sum(1 for t in tasks if t.priority == "High" and not t.completed),
        upcoming_deadlines=sum(1 for t in tasks if not t.completed),
    )

@router.get("/tasks/{item_id}", response_model=TaskRead)
def get_task(item_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_owned(db, Task, item_id, current_user.id)

@router.post("/tasks", response_model=TaskRead, status_code=201)
def create_task(payload: TaskCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = Task(user_id=current_user.id, **payload.model_dump())
    db.add(item); db.commit(); db.refresh(item); return item

@router.put("/tasks/{item_id}", response_model=TaskRead)
def update_task(item_id: int, payload: TaskUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = get_owned(db, Task, item_id, current_user.id); update_model(item, payload); db.commit(); db.refresh(item); return item

@router.put("/tasks/{item_id}/complete", response_model=TaskRead)
def complete_task(item_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = get_owned(db, Task, item_id, current_user.id)
    item.completed = True
    db.commit(); db.refresh(item); return item

@router.put("/tasks/{item_id}/reopen", response_model=TaskRead)
def reopen_task(item_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = get_owned(db, Task, item_id, current_user.id)
    item.completed = False
    db.commit(); db.refresh(item); return item

@router.delete("/tasks/{item_id}")
def delete_task(item_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = get_owned(db, Task, item_id, current_user.id); db.delete(item); db.commit(); return {"message": "Task deleted"}

@router.get("/study-sessions", response_model=list[StudySessionRead])
def list_sessions(
    session_date: str | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(StudySession).filter(StudySession.user_id == current_user.id)
    if session_date:
        query = query.filter(StudySession.session_date == session_date)
    if search:
        like = f"%{search.strip()}%"
        query = query.filter((StudySession.subject.ilike(like)) | (StudySession.duration.ilike(like)) | (StudySession.reminder.ilike(like)))
    return query.order_by(StudySession.session_date.asc(), StudySession.start_time.asc(), StudySession.id.desc()).all()

@router.get("/study-sessions/summary")
def study_session_summary(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    sessions = db.query(StudySession).filter(StudySession.user_id == current_user.id).all()
    unique_days = len(set(s.session_date for s in sessions))
    return {
        "total_sessions": len(sessions),
        "planned_days": unique_days,
        "reminders_enabled": sum(1 for s in sessions if s.reminder and s.reminder.lower() != "none"),
        "upcoming_sessions": len(sessions),
    }

@router.get("/study-sessions/{item_id}", response_model=StudySessionRead)
def get_session(item_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_owned(db, StudySession, item_id, current_user.id)

@router.post("/study-sessions", response_model=StudySessionRead, status_code=201)
def create_session(payload: StudySessionCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = StudySession(user_id=current_user.id, **payload.model_dump())
    db.add(item); db.commit(); db.refresh(item); return item

@router.put("/study-sessions/{item_id}", response_model=StudySessionRead)
def update_session(item_id: int, payload: StudySessionUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = get_owned(db, StudySession, item_id, current_user.id); update_model(item, payload); db.commit(); db.refresh(item); return item

@router.put("/study-sessions/{item_id}/reminder", response_model=StudySessionRead)
def update_session_reminder(item_id: int, payload: StudySessionUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = get_owned(db, StudySession, item_id, current_user.id)
    if payload.reminder is not None:
        item.reminder = payload.reminder
    db.commit(); db.refresh(item); return item

@router.delete("/study-sessions/{item_id}")
def delete_session(item_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = get_owned(db, StudySession, item_id, current_user.id); db.delete(item); db.commit(); return {"message": "Study session deleted"}

@router.get("/progress", response_model=list[ProgressRead])
def list_progress(
    status: str | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(ProgressEntry).filter(ProgressEntry.user_id == current_user.id)
    if status and status != "All":
        query = query.filter(ProgressEntry.status == status)
    if search:
        like = f"%{search.strip()}%"
        query = query.filter((ProgressEntry.task.ilike(like)) | (ProgressEntry.score.ilike(like)) | (ProgressEntry.status.ilike(like)))
    return query.order_by(ProgressEntry.id.desc()).all()

@router.get("/progress/summary")
def progress_summary(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    entries = db.query(ProgressEntry).filter(ProgressEntry.user_id == current_user.id).all()
    tasks = db.query(Task).filter(Task.user_id == current_user.id).all()
    completed_tasks = sum(1 for t in tasks if t.completed)
    total_study_hours = sum(float(p.study_hours or 0) for p in entries)
    completed_entries = sum(1 for p in entries if p.status == "Completed")
    active_goals = db.query(Goal).filter(Goal.user_id == current_user.id, Goal.status == "Active").count()
    avg_score = 0
    numeric_scores = []
    for p in entries:
        cleaned = str(p.score).replace("%", "").strip()
        try:
            numeric_scores.append(float(cleaned))
        except ValueError:
            pass
    if numeric_scores:
        avg_score = round(sum(numeric_scores) / len(numeric_scores), 1)
    return {
        "completed_tasks": completed_tasks,
        "total_study_hours": round(total_study_hours, 1),
        "progress_entries": len(entries),
        "completed_entries": completed_entries,
        "active_goals": active_goals,
        "average_score": avg_score,
    }

@router.get("/progress/weekly-stats")
def weekly_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    entries = db.query(ProgressEntry).filter(ProgressEntry.user_id == current_user.id).all()
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    stats = []
    for day in days:
        day_entries = [p for p in entries if p.week_day == day]
        stats.append({
            "day": day,
            "study_hours": round(sum(float(p.study_hours or 0) for p in day_entries), 1),
            "completed": sum(1 for p in day_entries if p.status == "Completed"),
            "entries": len(day_entries),
        })
    return stats

@router.get("/course-progress")
def course_progress(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    courses = db.query(Course).filter(Course.user_id == current_user.id, Course.archived == False).order_by(Course.progress.desc()).all()
    return [
        {
            "id": c.id,
            "name": c.name,
            "instructor": c.instructor,
            "semester": c.semester,
            "progress": c.progress,
            "status": "Excellent" if c.progress >= 80 else "Good" if c.progress >= 50 else "Needs Attention",
        }
        for c in courses
    ]

@router.post("/progress", response_model=ProgressRead, status_code=201)
def create_progress(payload: ProgressCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    data = payload.model_dump()
    data["week_day"] = _week_day_from_entry_date(data.get("entry_date"))
    item = ProgressEntry(user_id=current_user.id, **data)
    db.add(item); db.commit(); db.refresh(item); return item

@router.put("/progress/{item_id}", response_model=ProgressRead)
def update_progress(item_id: int, payload: ProgressUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = get_owned(db, ProgressEntry, item_id, current_user.id)
    update_model(item, payload)
    item.week_day = _week_day_from_entry_date(item.entry_date)
    db.commit(); db.refresh(item); return item

@router.delete("/progress/{item_id}")
def delete_progress(item_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = get_owned(db, ProgressEntry, item_id, current_user.id); db.delete(item); db.commit(); return {"message": "Progress entry deleted"}

@router.get("/goals", response_model=list[GoalRead])
def list_goals(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Goal).filter(Goal.user_id == current_user.id).all()

@router.post("/goals", response_model=GoalRead, status_code=201)
def create_goal(payload: GoalCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = Goal(user_id=current_user.id, **payload.model_dump())
    db.add(item); db.commit(); db.refresh(item); return item

@router.put("/goals/{item_id}", response_model=GoalRead)
def update_goal(item_id: int, payload: GoalUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = get_owned(db, Goal, item_id, current_user.id); update_model(item, payload); db.commit(); db.refresh(item); return item

@router.delete("/goals/{item_id}")
def delete_goal(item_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = get_owned(db, Goal, item_id, current_user.id); db.delete(item); db.commit(); return {"message": "Goal deleted"}


@router.get("/notifications", response_model=list[NotificationRead])
def list_notifications(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    settings = _settings_for(db, current_user.id)
    notifications = []
    now_text = datetime.now().isoformat(timespec="seconds")

    if settings.task_reminders or settings.deadline_warnings:
        tasks = db.query(Task).filter(Task.user_id == current_user.id, Task.completed == False).order_by(Task.due_date.asc(), Task.id.desc()).all()
        for t in tasks:
            days = _days_until(t.due_date)
            if days is None:
                if settings.task_reminders:
                    notifications.append({
                        "id": f"task-{t.id}",
                        "title": "Task Reminder",
                        "message": f"{t.title} for {t.course} is still pending. Deadline: {t.due_date}.",
                        "type": "task",
                        "priority": t.priority,
                        "source_id": t.id,
                        "action_route": "/tasks",
                        "created_at": now_text,
                        "is_read": False,
                    })
            elif days < 0 and settings.deadline_warnings:
                notifications.append({
                    "id": f"overdue-task-{t.id}",
                    "title": "Overdue Task",
                    "message": f"{t.title} is overdue by {abs(days)} day(s). Update or complete it soon.",
                    "type": "deadline",
                    "priority": "High",
                    "source_id": t.id,
                    "action_route": "/tasks",
                    "created_at": now_text,
                    "is_read": False,
                })
            elif days <= 2 and settings.deadline_warnings:
                label = "today" if days == 0 else "tomorrow" if days == 1 else f"in {days} days"
                notifications.append({
                    "id": f"deadline-task-{t.id}",
                    "title": "Deadline Alert",
                    "message": f"{t.title} is due {label}. Priority: {t.priority}.",
                    "type": "deadline",
                    "priority": t.priority,
                    "source_id": t.id,
                    "action_route": "/tasks",
                    "created_at": now_text,
                    "is_read": False,
                })

    if settings.study_reminders:
        sessions = db.query(StudySession).filter(StudySession.user_id == current_user.id).order_by(StudySession.session_date.asc(), StudySession.start_time.asc()).all()
        for session in sessions[:8]:
            notifications.append({
                "id": f"study-{session.id}",
                "title": "Study Reminder",
                "message": f"{session.subject} session is planned on {session.session_date} at {session.start_time}. Reminder: {session.reminder}.",
                "type": "study",
                "priority": "Medium",
                "source_id": session.id,
                "action_route": "/planner",
                "created_at": now_text,
                "is_read": False,
            })

    if settings.weekly_summary:
        entries = db.query(ProgressEntry).filter(ProgressEntry.user_id == current_user.id).all()
        study_hours = round(sum(float(p.study_hours or 0) for p in entries), 1)
        completed = db.query(Task).filter(Task.user_id == current_user.id, Task.completed == True).count()
        notifications.append({
            "id": "weekly-summary",
            "title": "Weekly Progress Summary",
            "message": f"You have completed {completed} task(s) and recorded {study_hours} study hour(s).",
            "type": "summary",
            "priority": "Low",
            "source_id": None,
            "action_route": "/progress",
            "created_at": now_text,
            "is_read": False,
        })

    if not notifications:
        total_tasks = db.query(Task).filter(Task.user_id == current_user.id).count()
        active_courses = db.query(Course).filter(Course.user_id == current_user.id, Course.archived == False).count()

        if total_tasks == 0:
            notifications.append({
                "id": "welcome-task-tip",
                "title": "Add Your First Task",
                "message": "Start by adding a task to get deadline alerts and reminders on this screen.",
                "type": "task",
                "priority": "Low",
                "source_id": None,
                "action_route": "/addTask",
                "created_at": now_text,
                "is_read": False,
            })

        if active_courses == 0:
            notifications.append({
                "id": "welcome-course-tip",
                "title": "Add a Course",
                "message": "Create your first course so your tasks and progress can be organized better.",
                "type": "course",
                "priority": "Low",
                "source_id": None,
                "action_route": "/addCourse",
                "created_at": now_text,
                "is_read": False,
            })

        if not notifications:
            notifications.append({
                "id": "notifications-ready",
                "title": "Notifications Are Up to Date",
                "message": "You are all caught up for now. New reminders will appear here automatically.",
                "type": "summary",
                "priority": "Low",
                "source_id": None,
                "action_route": "/dashboard",
                "created_at": now_text,
                "is_read": False,
            })

    return notifications

@router.get("/notification-settings", response_model=NotificationSettingsRead)
def get_notification_settings(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = db.query(NotificationSetting).filter(NotificationSetting.user_id == current_user.id).first() or NotificationSetting(user_id=current_user.id)
    if item.id is None: db.add(item); db.commit(); db.refresh(item)
    return item

@router.put("/notification-settings", response_model=NotificationSettingsRead)
def update_notification_settings(payload: NotificationSettingsUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = db.query(NotificationSetting).filter(NotificationSetting.user_id == current_user.id).first() or NotificationSetting(user_id=current_user.id)
    update_model(item, payload); db.add(item); db.commit(); db.refresh(item); return item

@router.get("/app-settings", response_model=AppSettingsRead)
def get_app_settings(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = db.query(AppSetting).filter(AppSetting.user_id == current_user.id).first() or AppSetting(user_id=current_user.id)
    if item.id is None: db.add(item); db.commit(); db.refresh(item)
    return item

@router.put("/app-settings", response_model=AppSettingsRead)
def update_app_settings(payload: AppSettingsUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = db.query(AppSetting).filter(AppSetting.user_id == current_user.id).first() or AppSetting(user_id=current_user.id)
    update_model(item, payload); db.add(item); db.commit(); db.refresh(item); return item

@router.post("/feedback", response_model=FeedbackRead, status_code=201)
def submit_feedback(payload: FeedbackCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = Feedback(user_id=current_user.id, message=payload.message)
    db.add(item); db.commit(); db.refresh(item); return item

@router.get("/feedbacks", response_model=list[FeedbackRead])
def list_feedback(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Feedback).filter(Feedback.user_id == current_user.id).order_by(Feedback.id.desc()).all()

@router.put("/feedbacks/{item_id}", response_model=FeedbackRead)
def update_feedback(item_id: int, payload: FeedbackUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = get_owned(db, Feedback, item_id, current_user.id)
    item.message = payload.message
    db.commit(); db.refresh(item); return item

@router.delete("/feedbacks/{item_id}")
def delete_feedback(item_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = get_owned(db, Feedback, item_id, current_user.id)
    db.delete(item); db.commit(); return {"message": "Feedback deleted"}

@router.get("/help")
def help_support():
    return {
        "faqs": [
            {"question": "How do I add a task?", "answer": "Open Tasks and tap Add Task."},
            {"question": "How do I archive a course?", "answer": "Open a course and update archive status."},
            {"question": "How do reminders work?", "answer": "Set notification preferences in Notification Settings."},
        ],
        "support_email": "support@learnova.lk"
    }
