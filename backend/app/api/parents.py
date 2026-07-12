from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Any, List, Optional

from app.core.database import get_db
from app.crud import db_crud
from app.schemas.schemas import ParentOut, ParentUpdate, UserOut
from app.api.auth import get_current_active_user, check_role

router = APIRouter()

@router.get("/", response_model=List[ParentOut])
def read_parents(
    query: Optional[str] = None,
    school_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: UserOut = Depends(get_current_active_user)
) -> Any:
    target_school_id = school_id
    if current_user.role.name != "Super Admin":
        target_school_id = current_user.school_id

    db_query = db.query(db_crud.Parent)
    if target_school_id is not None:
        db_query = db_query.filter(db_crud.Parent.school_id == target_school_id)
        
    if query:
        db_query = db_query.filter(
            or_(
                db_crud.Parent.father_name.ilike(f"%{query}%"),
                db_crud.Parent.mother_name.ilike(f"%{query}%"),
                db_crud.Parent.father_mobile.ilike(f"%{query}%"),
                db_crud.Parent.mother_mobile.ilike(f"%{query}%")
            )
        )
    return db_query.all()

@router.get("/{parent_id}", response_model=ParentOut)
def read_parent(
    parent_id: int,
    db: Session = Depends(get_db),
    current_user: UserOut = Depends(get_current_active_user)
) -> Any:
    target_school_id = None
    if current_user.role.name != "Super Admin":
        target_school_id = current_user.school_id

    q = db.query(db_crud.Parent).filter(db_crud.Parent.id == parent_id)
    if target_school_id is not None:
        q = q.filter(db_crud.Parent.school_id == target_school_id)
        
    parent = q.first()
    if not parent:
        raise HTTPException(status_code=404, detail="Parent record not found")
    return parent

@router.put("/{parent_id}", response_model=ParentOut)
def update_parent(
    parent_id: int,
    parent_in: ParentUpdate,
    db: Session = Depends(get_db),
    current_user: UserOut = Depends(check_role(["Super Admin", "School Admin", "Teacher"]))
) -> Any:
    target_school_id = None
    if current_user.role.name != "Super Admin":
        target_school_id = current_user.school_id

    q = db.query(db_crud.Parent).filter(db_crud.Parent.id == parent_id)
    if target_school_id is not None:
        q = q.filter(db_crud.Parent.school_id == target_school_id)

    parent = q.first()
    if not parent:
        raise HTTPException(status_code=404, detail="Parent not found")
        
    update_data = parent_in.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(parent, field, val)
        
    db.commit()
    db.refresh(parent)
    db_crud.log_audit(db, user_id=current_user.id, action="UPDATE_PARENT", details=f"Updated parent ID {parent_id}")
    return parent
