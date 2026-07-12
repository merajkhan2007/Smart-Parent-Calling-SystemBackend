from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Any

from app.core.database import get_db
from app.core.config import settings
from app.core.security import verify_password, create_access_token, create_refresh_token, verify_token
from app.crud import db_crud
from app.schemas.schemas import Token, LoginRequest, UserOut, ForgotPasswordRequest

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> UserOut:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    email = verify_token(token, "access")
    if email is None:
        raise credentials_exception
    user = db_crud.get_user_by_email(db, email=email)
    if user is None:
        raise credentials_exception
    return user

def get_current_active_user(current_user: UserOut = Depends(get_current_user)) -> UserOut:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# Helper to verify permissions based on role
def check_role(allowed_roles: list):
    def dependency(current_user: UserOut = Depends(get_current_active_user)):
        if current_user.role.name not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource"
            )
        return current_user
    return dependency

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)) -> Any:
    user = db_crud.get_user_by_email(db, email=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password",
        )
    elif not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )
        
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(user.email, expires_delta=access_token_expires)
    refresh_token = create_refresh_token(user.email)
    
    db_crud.log_audit(db, user_id=user.id, action="LOGIN", details=f"User logged in: {user.email}")
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "role": user.role.name,
        "email": user.email,
        "name": user.full_name or user.email,
        "school_id": user.school_id
    }

@router.post("/login-json", response_model=Token)
def login_json(req: LoginRequest, db: Session = Depends(get_db)) -> Any:
    user = db_crud.get_user_by_email(db, email=req.email)
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password",
        )
    elif not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )
        
    # Standard or long expiry based on remember_me
    minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES if not req.remember_me else 60 * 24 * 30  # 30 days
    access_token = create_access_token(user.email, expires_delta=timedelta(minutes=minutes))
    refresh_token = create_refresh_token(user.email)
    
    db_crud.log_audit(db, user_id=user.id, action="LOGIN", details=f"User logged in via JSON (Remember me: {req.remember_me})")
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "role": user.role.name,
        "email": user.email,
        "name": user.full_name or user.email,
        "school_id": user.school_id
    }

@router.post("/refresh", response_model=Token)
def refresh_token(refresh_token: str, db: Session = Depends(get_db)) -> Any:
    email = verify_token(refresh_token, "refresh")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid refresh token",
        )
    user = db_crud.get_user_by_email(db, email=email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    elif not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )
        
    access_token = create_access_token(user.email)
    new_refresh_token = create_refresh_token(user.email)
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "role": user.role.name,
        "email": user.email,
        "name": user.full_name or user.email,
        "school_id": user.school_id
    }

@router.get("/me", response_model=UserOut)
def read_users_me(current_user: UserOut = Depends(get_current_active_user)) -> Any:
    return current_user

@router.post("/forgot-password")
def forgot_password(req: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db_crud.get_user_by_email(db, email=req.email)
    if not user:
        raise HTTPException(status_code=404, detail="Email address not found")
    # Simulate email sending or token generation
    db_crud.log_audit(db, user_id=user.id, action="FORGOT_PASSWORD", details="Password reset link requested")
    return {"message": "Password reset instructions sent to your email (simulated)"}
