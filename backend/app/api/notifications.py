from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any, List, Optional

from app.core.database import get_db
from app.crud import db_crud
from app.schemas.schemas import NotificationOut, UserOut
from app.api.auth import get_current_active_user

router = APIRouter()

@router.get("/", response_model=List[NotificationOut])
def read_notifications(
    unread_only: bool = False,
    school_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: UserOut = Depends(get_current_active_user)
) -> Any:
    target_school_id = school_id
    if current_user.role.name != "Super Admin":
        target_school_id = current_user.school_id

    query = db.query(db_crud.Notification)
    if target_school_id is not None:
        query = query.filter(db_crud.Notification.school_id == target_school_id)
    if unread_only:
        query = query.filter(db_crud.Notification.is_read == False)
    return query.order_by(db_crud.Notification.created_at.desc()).all()

@router.post("/mark-all-read")
def mark_all_read(
    db: Session = Depends(get_db),
    current_user: UserOut = Depends(get_current_active_user)
):
    target_school_id = None
    if current_user.role.name != "Super Admin":
        target_school_id = current_user.school_id

    q = db.query(db_crud.Notification).filter(db_crud.Notification.is_read == False)
    if target_school_id is not None:
        q = q.filter(db_crud.Notification.school_id == target_school_id)
    
    q.update({"is_read": True}, synchronize_session=False)
    db.commit()
    return {"message": "All notifications marked as read"}

@router.post("/{notification_id}/read")
def mark_single_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: UserOut = Depends(get_current_active_user)
):
    target_school_id = None
    if current_user.role.name != "Super Admin":
        target_school_id = current_user.school_id

    q = db.query(db_crud.Notification).filter(db_crud.Notification.id == notification_id)
    if target_school_id is not None:
        q = q.filter(db_crud.Notification.school_id == target_school_id)
        
    notif = q.first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    notif.is_read = True
    db.commit()
    return {"message": f"Notification {notification_id} marked as read"}
