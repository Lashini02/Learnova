from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.core.security import hash_password, verify_password
from app.db.session import get_db
from app.models.models import User
from app.schemas.schemas import UserRead, UserUpdate, ChangePasswordRequest

router = APIRouter(prefix="/profile", tags=["Profile"])

@router.get("/me", response_model=UserRead)
def my_profile(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("/me", response_model=UserRead)
def update_profile(payload: UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        data = payload.model_dump(exclude_unset=True)

        if "email" in data and data["email"]:
            new_email = str(data["email"]).lower()
            existing = db.query(User).filter(User.email == new_email, User.id != current_user.id).first()
            if existing:
                raise HTTPException(status_code=409, detail="Email already used by another account")
            data["email"] = new_email

        if "student_id" in data and data["student_id"]:
            existing = db.query(User).filter(User.student_id == data["student_id"], User.id != current_user.id).first()
            if existing:
                raise HTTPException(status_code=409, detail="Student ID already used by another account")

        for key, value in data.items():
            setattr(current_user, key, value)
        db.commit()
        db.refresh(current_user)
        return current_user
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to update profile: {str(e)}")

@router.put("/change-password")
def change_password(payload: ChangePasswordRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    if payload.new_password != payload.confirm_password:
        raise HTTPException(status_code=400, detail="New passwords do not match")
    current_user.password_hash = hash_password(payload.new_password)
    db.commit()
    return {"message": "Password changed successfully"}
