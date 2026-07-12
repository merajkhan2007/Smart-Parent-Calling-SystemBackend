from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.api.auth import get_current_active_user, check_role
from app.crud import db_crud
from app.schemas.schemas import SchoolOut, SchoolCreate

router = APIRouter()

# Restrict all school CRUD commands to Super Admin
super_admin_dependency = Depends(check_role(["Super Admin"]))

@router.get("/", response_model=List[SchoolOut], dependencies=[super_admin_dependency])
def list_schools(db: Session = Depends(get_db)):
    return db_crud.get_schools(db)

@router.post("/", response_model=SchoolOut, dependencies=[super_admin_dependency])
def register_school(req: SchoolCreate, db: Session = Depends(get_db)):
    existing = db_crud.get_school_by_name(db, name=req.name)
    if existing:
        raise HTTPException(status_code=400, detail="School with this name already exists")
    return db_crud.create_school(db, school_name=req.name, logo_url=req.logo_url)

@router.delete("/{school_id}", dependencies=[super_admin_dependency])
def remove_school(school_id: int, db: Session = Depends(get_db)):
    success = db_crud.delete_school(db, school_id=school_id)
    if not success:
        raise HTTPException(status_code=404, detail="School registry not found")
    return {"message": "School and all its associated data deleted"}
