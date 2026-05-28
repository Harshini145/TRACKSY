from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.database import get_db
from core.security import get_current_user
from models.user import Notification, User

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("/")
def list_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(Notification)
        .filter(Notification.user_id == current_user.user_id)
        .order_by(Notification.created_at.desc())
        .limit(50)
        .all()
    )


@router.delete("/{notification_id}", status_code=204)
def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notif = db.query(Notification).filter(
        Notification.notification_id == notification_id,
        Notification.user_id == current_user.user_id,
    ).first()
    if notif:
        db.delete(notif)
        db.commit()
