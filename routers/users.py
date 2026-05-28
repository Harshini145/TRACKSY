from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from core.database import get_db
from core.security import get_current_user
from models.user import UserSetting, User

router = APIRouter(prefix="/users", tags=["Users"])


class SettingsUpdate(BaseModel):
    theme: str


@router.get("/me")
def get_profile(current_user: User = Depends(get_current_user)):
    return {
        "user_id": current_user.user_id,
        "username": current_user.username,
        "email": current_user.email,
        "created_at": current_user.created_at,
    }


@router.get("/settings")
def get_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    s = db.query(UserSetting).filter(UserSetting.user_id == current_user.user_id).first()
    return {"theme": s.theme if s else "light"}


@router.put("/settings")
def update_settings(
    payload: SettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    s = db.query(UserSetting).filter(UserSetting.user_id == current_user.user_id).first()
    if s:
        s.theme = payload.theme
    else:
        db.add(UserSetting(user_id=current_user.user_id, theme=payload.theme))
    db.commit()
    return {"theme": payload.theme}
