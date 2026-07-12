from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Any, Optional

from app.core.database import get_db
from app.crud import db_crud
from app.schemas.schemas import UserOut, UserCreate, UserUpdate
from app.api.auth import check_role

router = APIRouter()

# Allow Super Admin & School Admin
admin_role_dependency = Depends(check_role(["Super Admin", "School Admin"]))

@router.get("/", response_model=List[UserOut])
def read_users(
    school_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: UserOut = Depends(admin_role_dependency)
) -> Any:
    # Resolve target school scope
    target_school_id = school_id
    if current_user.role.name != "Super Admin":
        target_school_id = current_user.school_id
    return db_crud.get_users(db, school_id=target_school_id)

@router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    current_user: UserOut = Depends(admin_role_dependency)
) -> Any:
    # Restrict role creations by School Admins
    if current_user.role.name != "Super Admin":
        # Force creator's school context
        user_in.school_id = current_user.school_id
        # School admins cannot create Super Admins
        role = db.query(db_crud.Role).filter(db_crud.Role.id == user_in.role_id).first()
        if role and role.name == "Super Admin":
            raise HTTPException(status_code=403, detail="Cannot register global Super Admin accounts")

    # Check if user email already exists
    existing = db_crud.get_user_by_email(db, email=user_in.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists"
        )
    user = db_crud.create_user(db, user=user_in)
    db_crud.log_audit(db, user_id=current_user.id, action="CREATE_USER", details=f"Created user: {user.email} in school {user.school_id}")
    return user

@router.put("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    current_user: UserOut = Depends(admin_role_dependency)
) -> Any:
    user = db_crud.get_user_by_id(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Restrict modifications by School Admins
    if current_user.role.name != "Super Admin":
        if user.school_id != current_user.school_id:
            raise HTTPException(status_code=403, detail="Access denied to this user record")
        # Enforce target role limits
        if user_in.role_id:
            role = db.query(db_crud.Role).filter(db_crud.Role.id == user_in.role_id).first()
            if role and role.name == "Super Admin":
                raise HTTPException(status_code=403, detail="Cannot assign Super Admin privilege")
        # School admins cannot change user school contexts
        user_in.school_id = current_user.school_id

    # Check if updated email conflicts with another user
    if user_in.email and user_in.email != user.email:
        existing = db_crud.get_user_by_email(db, email=user_in.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email already exists"
            )
            
    updated_user = db_crud.update_user(db, db_user=user, user_in=user_in)
    db_crud.log_audit(db, user_id=current_user.id, action="UPDATE_USER", details=f"Updated user ID: {user_id}")
    return updated_user

@router.delete("/{user_id}", status_code=status.HTTP_200_OK)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: UserOut = Depends(admin_role_dependency)
) -> Any:
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete your own account"
        )
    user = db_crud.get_user_by_id(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Restrict deletions by School Admins
    if current_user.role.name != "Super Admin" and user.school_id != current_user.school_id:
        raise HTTPException(status_code=403, detail="Access denied to this user record")

    db_crud.delete_user(db, user_id=user_id)
    db_crud.log_audit(db, user_id=current_user.id, action="DELETE_USER", details=f"Deleted user ID: {user_id}")
    return {"message": "User successfully deleted"}
