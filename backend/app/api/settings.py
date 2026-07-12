from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import Any, Optional

from app.core.database import get_db
from app.crud import db_crud
from app.schemas.schemas import SettingsOut, SettingsUpdate, UserOut
from app.api.auth import get_current_active_user, check_role

router = APIRouter()

@router.get("/", response_model=SettingsOut)
def read_settings(
    school_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: UserOut = Depends(get_current_active_user)
) -> Any:
    target_school_id = school_id
    if current_user.role.name != "Super Admin":
        target_school_id = current_user.school_id
    return db_crud.get_settings(db, school_id=target_school_id)

@router.put("/", response_model=SettingsOut)
def update_settings(
    settings_in: SettingsUpdate,
    school_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: UserOut = Depends(check_role(["Super Admin", "School Admin"]))
) -> Any:
    target_school_id = school_id
    if current_user.role.name != "Super Admin":
        target_school_id = current_user.school_id

    db_settings = db_crud.get_settings(db, school_id=target_school_id)
    
    update_data = settings_in.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(db_settings, field, val)
        
    db.commit()
    db.refresh(db_settings)
    db_crud.log_audit(db, user_id=current_user.id, action="UPDATE_SETTINGS", details=f"Updated system settings for school {target_school_id}")
    return db_settings

@router.post("/logo", response_model=SettingsOut)
def upload_logo(
    file: UploadFile = File(...),
    school_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: UserOut = Depends(check_role(["Super Admin", "School Admin"]))
):
    if not file.filename.endswith(('.png', '.jpg', '.jpeg', '.svg')):
        raise HTTPException(status_code=400, detail="Invalid file extension. Please select an image.")
        
    target_school_id = school_id
    if current_user.role.name != "Super Admin":
        target_school_id = current_user.school_id

    db_settings = db_crud.get_settings(db, school_id=target_school_id)
    db_settings.logo_url = f"/uploads/{file.filename}"
    db.commit()
    db.refresh(db_settings)
    
    db_crud.log_audit(db, user_id=current_user.id, action="UPLOAD_LOGO", details=f"Uploaded logo: {file.filename} for school {target_school_id}")
    return db_settings
