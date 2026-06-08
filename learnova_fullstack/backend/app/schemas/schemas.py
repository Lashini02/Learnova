from datetime import datetime
import re
from pydantic import BaseModel, EmailStr, Field
from pydantic import field_validator

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserBase(BaseModel):
    name: str
    email: EmailStr
    role: str = "Student"
    course: str = "BSc Undergraduate"
    student_id: str | None = None
    profile_picture: str | None = None

class UserCreate(UserBase):
    password: str = Field(min_length=6)

class UserLogin(BaseModel):
    # Accept either an email address or a student ID, e.g. student@learnova.lk OR LEA-2026-001
    identifier: str = Field(min_length=3)
    password: str

    @field_validator("identifier")
    @classmethod
    def validate_identifier(cls, value: str) -> str:
        identifier = value.strip()
        if not identifier:
            raise ValueError("Email / Student ID is required")

        # Allowed: valid Gmail address
        gmail_pattern = re.compile(r"^[A-Za-z0-9._%+-]+@gmail\.com$", re.IGNORECASE)
        # Allowed student ID format: ITBNM-2313 0010 (example)
        student_id_pattern = re.compile(r"^[A-Za-z]{2,12}-\d{4}\s\d{4}$")
        # Allowed institutional format: ITBNM-2313 0010@horizoncampus.edu.lk
        horizon_email_pattern = re.compile(
            r"^[A-Za-z]{2,12}-\d{4}\s\d{4}@horizoncampus\.edu\.lk$",
            re.IGNORECASE,
        )

        if (
            gmail_pattern.fullmatch(identifier)
            or student_id_pattern.fullmatch(identifier)
            or horizon_email_pattern.fullmatch(identifier)
        ):
            return identifier

        raise ValueError(
            "Use a valid Gmail or format like ITBNM-2313 0010 / ITBNM-2313 0010@horizoncampus.edu.lk"
        )

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    new_password: str = Field(min_length=6)
    confirm_password: str = Field(min_length=6)

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=6)
    confirm_password: str = Field(min_length=6)

class UserRead(UserBase):
    id: int
    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    course: str | None = None
    student_id: str | None = None
    profile_picture: str | None = None

class CourseBase(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    instructor: str = Field(min_length=2, max_length=160)
    semester: str = Field(min_length=2, max_length=80)
    description: str = ""
    progress: float = Field(default=0.0, ge=0.0, le=100.0)
    archived: bool = False
class CourseCreate(CourseBase): pass
class CourseUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=160)
    instructor: str | None = Field(default=None, min_length=2, max_length=160)
    semester: str | None = Field(default=None, min_length=2, max_length=80)
    description: str | None = None
    progress: float | None = Field(default=None, ge=0.0, le=100.0)
    archived: bool | None = None
class CourseRead(CourseBase):
    id: int
    class Config:
        from_attributes = True

class TaskBase(BaseModel):
    title: str = Field(min_length=2, max_length=180)
    course: str = Field(min_length=2, max_length=160)
    due_date: str = Field(min_length=4, max_length=80)
    priority: str = Field(default="Medium", pattern="^(High|Medium|Low)$")
    description: str = ""
    completed: bool = False
class TaskCreate(TaskBase): pass
class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=180)
    course: str | None = Field(default=None, min_length=2, max_length=160)
    due_date: str | None = Field(default=None, min_length=4, max_length=80)
    priority: str | None = Field(default=None, pattern="^(High|Medium|Low)$")
    description: str | None = None
    completed: bool | None = None
class TaskRead(TaskBase):
    id: int
    class Config:
        from_attributes = True

class TaskSummary(BaseModel):
    total: int
    pending: int
    completed: int
    high_priority: int
    upcoming_deadlines: int

class StudySessionBase(BaseModel):
    subject: str
    session_date: str = "Today"
    start_time: str
    duration: str
    reminder: str = "15 minutes before"
class StudySessionCreate(StudySessionBase): pass
class StudySessionUpdate(BaseModel):
    subject: str | None = None
    session_date: str | None = None
    start_time: str | None = None
    duration: str | None = None
    reminder: str | None = None
class StudySessionRead(StudySessionBase):
    id: int
    class Config:
        from_attributes = True

class ProgressBase(BaseModel):
    task: str = Field(min_length=2, max_length=180)
    score: str = Field(min_length=1, max_length=50)
    status: str = Field(default="Completed", pattern="^(Completed|In Progress|Pending|Needs Review)$")
    study_hours: float = Field(default=0.0, ge=0.0)
    entry_date: str = "Today"
    week_day: str = Field(default="Mon", pattern="^(Mon|Tue|Wed|Thu|Fri|Sat|Sun)$")
class ProgressCreate(ProgressBase): pass
class ProgressUpdate(BaseModel):
    task: str | None = Field(default=None, min_length=2, max_length=180)
    score: str | None = Field(default=None, min_length=1, max_length=50)
    status: str | None = Field(default=None, pattern="^(Completed|In Progress|Pending|Needs Review)$")
    study_hours: float | None = Field(default=None, ge=0.0)
    entry_date: str | None = None
    week_day: str | None = Field(default=None, pattern="^(Mon|Tue|Wed|Thu|Fri|Sat|Sun)$")
class ProgressRead(ProgressBase):
    id: int
    class Config:
        from_attributes = True

class GoalBase(BaseModel):
    title: str
    target_date: str = "This semester"
    status: str = "Active"
class GoalCreate(GoalBase): pass
class GoalUpdate(BaseModel):
    title: str | None = None
    target_date: str | None = None
    status: str | None = None
class GoalRead(GoalBase):
    id: int
    class Config:
        from_attributes = True

class NotificationRead(BaseModel):
    id: str
    title: str
    message: str
    type: str
    priority: str = "Medium"
    source_id: int | None = None
    action_route: str | None = None
    created_at: str
    is_read: bool = False

class NotificationSettingsRead(BaseModel):
    task_reminders: bool = True
    study_reminders: bool = True
    deadline_warnings: bool = True
    weekly_summary: bool = True
    email_notifications: bool = False
    notification_time: str = "08:00"
    class Config:
        from_attributes = True
class NotificationSettingsUpdate(BaseModel):
    task_reminders: bool | None = None
    study_reminders: bool | None = None
    deadline_warnings: bool | None = None
    weekly_summary: bool | None = None
    email_notifications: bool | None = None
    notification_time: str | None = None

class AppSettingsRead(BaseModel):
    theme: str = "Light"
    language: str = "English"
    class Config:
        from_attributes = True
class AppSettingsUpdate(AppSettingsRead): pass

class FeedbackCreate(BaseModel):
    message: str
class FeedbackUpdate(BaseModel):
    message: str
class FeedbackRead(BaseModel):
    id: int
    message: str
    created_at: datetime | None = None
    class Config:
        from_attributes = True

class DashboardSummary(BaseModel):
    student_name: str
    today_tasks: int
    pending_tasks: int
    completed_tasks: int
    upcoming_deadlines: int
    active_courses: int
    study_sessions: int
    total_study_hours: float
    up_next: list[TaskRead] = Field(default_factory=list)
