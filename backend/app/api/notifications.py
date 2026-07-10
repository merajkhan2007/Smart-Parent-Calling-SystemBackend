from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Any, List

from app.core.database import get_db
from app.crud import db_crud
from app.schemas.schemas import NotificationOut, UserOut
from app.api.auth import get_current_active_user

router = APIRouter()

@router.get("/", response_model=List[NotificationOut])
def read_notifications(
    unread_only: bool = False,
    db: Session = Depends(get_db),
    current_user: UserOut = Depends(get_current_active_user)
) -> Any:
    query = db.query(db_crud.Notification)
    if unread_only:
        query = query.filter(db_crud.Notification.is_read == False)
    return query.order_by(db_crud.Notification.created_at.desc()).all()

@router.post("/mark-all-read")
def mark_all_read(
    db: Session = Depends(get_db),
    current_user: UserOut = Depends(get_current_active_user)
):
    db.query(db_crud.Notification).filter(db_crud.Notification.is_read == False).update({"is_read": True})
    db.commit()
    return {"message": "All notifications marked as read"}

@router.post("/{notification_id}/read")
def mark_single_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: UserOut = Depends(get_current_active_user)
):
    notif = db.query(db_crud.Notification).filter(db_crud.Notification.id == notification_id).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    notif.is_read = True
    db.commit()
    return {"message": f"Notification {notification_id} marked as read"}
