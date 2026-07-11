from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Any

from app.core.database import get_db
from app.crud import db_crud
from app.schemas.schemas import UserOut, UserCreate, UserUpdate
from app.api.auth import check_role

router = APIRouter()

@router.get("/", response_model=List[UserOut])
def read_users(
    db: Session = Depends(get_db),
    current_user: UserOut = Depends(check_role(["Super Admin"]))
) -> Any:
    """
    Retrieve all users. Restricted to Super Admin.
    """
    return db_crud.get_users(db)

@router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    current_user: UserOut = Depends(check_role(["Super Admin"]))
) -> Any:
    """
    Create a new user. Restricted to Super Admin.
    """
    # Check if user email already exists
    existing = db_crud.get_user_by_email(db, email=user_in.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists"
        )
    user = db_crud.create_user(db, user=user_in)
    db_crud.log_audit(db, user_id=current_user.id, action="CREATE_USER", details=f"Created user: {user.email}")
    return user

@router.put("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    current_user: UserOut = Depends(check_role(["Super Admin"]))
) -> Any:
    """
    Update a user. Restricted to Super Admin.
    """
    user = db_crud.get_user_by_id(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
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
    current_user: UserOut = Depends(check_role(["Super Admin"]))
) -> Any:
    """
    Delete a user. Restricted to Super Admin.
    """
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Super Admin cannot delete their own account"
        )
    success = db_crud.delete_user(db, user_id=user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    db_crud.log_audit(db, user_id=current_user.id, action="DELETE_USER", details=f"Deleted user ID: {user_id}")
    return {"message": "User successfully deleted"}
