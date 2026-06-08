from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, Time, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(180), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(30), default="Student")
    course: Mapped[str] = mapped_column(String(120), default="BSc Undergraduate")
    student_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    profile_picture: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    courses = relationship("Course", back_populates="owner", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="owner", cascade="all, delete-orphan")
    sessions = relationship("StudySession", back_populates="owner", cascade="all, delete-orphan")
    progress_entries = relationship("ProgressEntry", back_populates="owner", cascade="all, delete-orphan")

class Course(Base):
    __tablename__ = "courses"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String(160))
    instructor: Mapped[str] = mapped_column(String(160))
    semester: Mapped[str] = mapped_column(String(80))
    description: Mapped[str] = mapped_column(Text, default="")
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    archived: Mapped[bool] = mapped_column(Boolean, default=False)
    owner = relationship("User", back_populates="courses")

class Task(Base):
    __tablename__ = "tasks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(180))
    course: Mapped[str] = mapped_column(String(160))
    due_date: Mapped[str] = mapped_column(String(80))
    priority: Mapped[str] = mapped_column(String(30), default="Medium")
    description: Mapped[str] = mapped_column(Text, default="")
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    owner = relationship("User", back_populates="tasks")

class StudySession(Base):
    __tablename__ = "study_sessions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    subject: Mapped[str] = mapped_column(String(160))
    session_date: Mapped[str] = mapped_column(String(40), default="Today")
    start_time: Mapped[str] = mapped_column(String(40))
    duration: Mapped[str] = mapped_column(String(80))
    reminder: Mapped[str] = mapped_column(String(100), default="15 minutes before")
    owner = relationship("User", back_populates="sessions")

class ProgressEntry(Base):
    __tablename__ = "progress_entries"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    task: Mapped[str] = mapped_column(String(180))
    score: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(80))
    study_hours: Mapped[float] = mapped_column(Float, default=0.0)
    entry_date: Mapped[str] = mapped_column(String(80), default="Today")
    week_day: Mapped[str] = mapped_column(String(20), default="Mon")
    owner = relationship("User", back_populates="progress_entries")

class Goal(Base):
    __tablename__ = "goals"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(180))
    target_date: Mapped[str] = mapped_column(String(80), default="This semester")
    status: Mapped[str] = mapped_column(String(80), default="Active")

class NotificationSetting(Base):
    __tablename__ = "notification_settings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    task_reminders: Mapped[bool] = mapped_column(Boolean, default=True)
    study_reminders: Mapped[bool] = mapped_column(Boolean, default=True)
    deadline_warnings: Mapped[bool] = mapped_column(Boolean, default=True)
    weekly_summary: Mapped[bool] = mapped_column(Boolean, default=True)
    email_notifications: Mapped[bool] = mapped_column(Boolean, default=False)
    notification_time: Mapped[str] = mapped_column(String(20), default="08:00")

class AppSetting(Base):
    __tablename__ = "app_settings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    theme: Mapped[str] = mapped_column(String(30), default="Light")
    language: Mapped[str] = mapped_column(String(30), default="English")

class Feedback(Base):
    __tablename__ = "feedback"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    message: Mapped[str] = mapped_column(Text)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
