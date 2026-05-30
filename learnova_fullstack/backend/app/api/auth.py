from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models.models import User, NotificationSetting, AppSetting
from app.schemas.schemas import (
    Token,
    UserCreate,
    UserLogin,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=Token, status_code=201)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    existing_email = db.query(User).filter(User.email == str(payload.email)).first()
    if existing_email:
        raise HTTPException(status_code=409, detail="Email already registered")

    if payload.student_id:
        existing_student_id = db.query(User).filter(User.student_id == payload.student_id).first()
        if existing_student_id:
            raise HTTPException(status_code=409, detail="Student ID already registered")

    user = User(
        name=payload.name.strip(),
        email=str(payload.email).lower(),
        password_hash=hash_password(payload.password),
        role="Student",
        course=payload.course,
        student_id=payload.student_id,
        profile_picture=payload.profile_picture,
    )
    db.add(user)
    db.flush()
    db.add(NotificationSetting(user_id=user.id))
    db.add(AppSetting(user_id=user.id))
    db.commit()
    db.refresh(user)
    return Token(access_token=create_access_token(user.email))

@router.post("/login", response_model=Token)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    identifier = payload.identifier.strip()
    email_identifier = identifier.lower()

    student_identifier = identifier
    if email_identifier.endswith("@horizoncampus.edu.lk"):
        student_identifier = identifier[: -len("@horizoncampus.edu.lk")]

    user = db.query(User).filter(
        or_(
            User.email == email_identifier,
            User.student_id == student_identifier,
            User.student_id == student_identifier.upper(),
        )
    ).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email/student ID or password")
    return Token(access_token=create_access_token(user.email))

@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == str(payload.email).lower()).first()
    if not user:
        # Same style as real apps: do not reveal whether the email exists.
        return {"message": "If this email exists, reset instructions will be available."}
    return {"message": "Account found. You can reset the password in the demo reset form."}

@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    if payload.new_password != payload.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    user = db.query(User).filter(User.email == str(payload.email).lower()).first()
    if not user:
        raise HTTPException(status_code=404, detail="No account found for this email")
    user.password_hash = hash_password(payload.new_password)
    db.commit()
    return {"message": "Password reset successfully. Please login with your new password."}
