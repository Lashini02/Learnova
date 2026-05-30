from sqlalchemy.orm import Session
from app.core.security import hash_password
from app.models.models import User, Course, Task, StudySession, ProgressEntry, Goal, NotificationSetting, AppSetting

def seed_demo_data(db: Session):
    user = db.query(User).filter(User.email == "student@learnova.lk").first()
    if user:
        return
    user = User(
        name="Sandali Wijerathna",
        email="student@learnova.lk",
        password_hash=hash_password("password123"),
        role="Student",
        course="BSc Undergraduate",
        student_id="LEA-2026-001",
    )
    db.add(user)
    db.flush()
    db.add_all([
        Course(user_id=user.id, name="Mobile App Development", instructor="Ms. Perera", semester="Year 2 - Semester 2", description="Flutter UI, navigation, forms and REST API integration.", progress=72),
        Course(user_id=user.id, name="Database Systems", instructor="Mr. Silva", semester="Year 2 - Semester 2", description="SQL, relational modeling and data management.", progress=58),
        Course(user_id=user.id, name="Software Engineering", instructor="Dr. Fernando", semester="Year 2 - Semester 2", description="Requirements, project planning and testing.", progress=84),
        Task(user_id=user.id, title="Submit UI wireframes", course="Mobile App Development", due_date="Today, 6.00 PM", priority="High", description="Finalize Learnova screens and attach screenshots.", completed=False),
        Task(user_id=user.id, title="Database quiz revision", course="Database Systems", due_date="Tomorrow", priority="Medium", description="Revise normalization and SQL joins.", completed=False),
        Task(user_id=user.id, title="Project report update", course="Software Engineering", due_date="Friday", priority="High", description="Update objectives, implementation and backend API section.", completed=True),
        StudySession(user_id=user.id, subject="Flutter forms", session_date="Today", start_time="8.00 AM", duration="1 hour", reminder="15 minutes before"),
        StudySession(user_id=user.id, subject="Database SQL", session_date="Today", start_time="4.00 PM", duration="45 minutes", reminder="10 minutes before"),
        ProgressEntry(user_id=user.id, task="UI Design", score="85%", status="Completed", study_hours=4.5),
        ProgressEntry(user_id=user.id, task="Backend API", score="70%", status="In Progress", study_hours=3.0),
        Goal(user_id=user.id, title="Complete all assignments before deadlines", target_date="This semester", status="Active"),
        NotificationSetting(user_id=user.id),
        AppSetting(user_id=user.id),
    ])
    db.commit()
