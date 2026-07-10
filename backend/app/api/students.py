from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import pandas as pd
import io
from typing import Any, List, Optional, Dict

from app.core.database import get_db
from app.crud import db_crud
from app.schemas.schemas import StudentOut, StudentCreate, StudentUpdate, UserOut
from app.api.auth import get_current_active_user, check_role

router = APIRouter()

@router.get("/", response_model=Dict[str, Any])
def read_students(
    query: Optional[str] = None,
    class_name: Optional[str] = None,
    section: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: UserOut = Depends(get_current_active_user)
) -> Any:
    skip = (page - 1) * limit
    students, total = db_crud.search_students(
        db, query=query, class_name=class_name, section=section, status=status, skip=skip, limit=limit
    )
    return {
        "students": students,
        "total": total,
        "page": page,
        "limit": limit
    }

@router.get("/{student_id}", response_model=StudentOut)
def read_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: UserOut = Depends(get_current_active_user)
) -> Any:
    student = db_crud.get_student(db, student_id=student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student

@router.post("/", response_model=StudentOut, status_code=status.HTTP_201_CREATED)
def create_student(
    student_in: StudentCreate,
    db: Session = Depends(get_db),
    current_user: UserOut = Depends(check_role(["Super Admin", "School Admin"]))
) -> Any:
    # Check if student admission number exists
    existing = db.query(db_crud.Student).filter(db_crud.Student.admission_number == student_in.admission_number).first()
    if existing:
        raise HTTPException(status_code=400, detail="Student with this admission number already exists")
    
    student = db_crud.create_student(db, student_in=student_in)
    db_crud.log_audit(db, user_id=current_user.id, action="CREATE_STUDENT", details=f"Created student: {student.name} ({student.admission_number})")
    return student

@router.put("/{student_id}", response_model=StudentOut)
def update_student(
    student_id: int,
    student_in: StudentUpdate,
    db: Session = Depends(get_db),
    current_user: UserOut = Depends(check_role(["Super Admin", "School Admin", "Teacher"]))
) -> Any:
    student = db_crud.update_student(db, student_id=student_id, student_in=student_in)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    db_crud.log_audit(db, user_id=current_user.id, action="UPDATE_STUDENT", details=f"Updated student ID {student_id}")
    return student

@router.delete("/{student_id}", status_code=status.HTTP_200_OK)
def delete_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: UserOut = Depends(check_role(["Super Admin", "School Admin"]))
) -> Any:
    success = db_crud.delete_student(db, student_id=student_id)
    if not success:
        raise HTTPException(status_code=404, detail="Student not found")
    db_crud.log_audit(db, user_id=current_user.id, action="DELETE_STUDENT", details=f"Deleted student ID {student_id}")
    return {"message": "Student successfully deleted"}

# --- EXCEL EXPORT ---
@router.get("/export/excel")
def export_students_excel(
    db: Session = Depends(get_db),
    current_user: UserOut = Depends(get_current_active_user)
):
    students = db.query(db_crud.Student).all()
    
    data = []
    for s in students:
        rfid_uid = s.rfid_card.uid if s.rfid_card else ""
        father_name = s.parent.father_name if s.parent else ""
        father_mobile = s.parent.father_mobile if s.parent else ""
        mother_name = s.parent.mother_name if s.parent else ""
        mother_mobile = s.parent.mother_mobile if s.parent else ""
        
        data.append({
            "Admission Number": s.admission_number,
            "Roll Number": s.roll_number,
            "Name": s.name,
            "Class": s.class_name,
            "Section": s.section,
            "Gender": s.gender,
            "DOB": s.dob,
            "Address": s.address,
            "RFID Card UID": rfid_uid,
            "Status": s.status,
            "Father Name": father_name,
            "Father Mobile": father_mobile,
            "Mother Name": mother_name,
            "Mother Mobile": mother_mobile
        })
        
    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Students", index=False)
    output.seek(0)
    
    headers = {
        'Content-Disposition': 'attachment; filename="students_list.xlsx"'
    }
    return StreamingResponse(
        output,
        headers=headers,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# --- EXCEL BULK IMPORT ---
@router.post("/import/excel")
def import_students_excel(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: UserOut = Depends(check_role(["Super Admin", "School Admin"]))
):
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Only Excel files (.xlsx, .xls) are allowed.")
        
    try:
        contents = file.file.read()
        df = pd.read_excel(io.BytesIO(contents))
        
        # Check required columns
        required_cols = ["Admission Number", "Name", "Class", "Section", "Father Name", "Father Mobile", "Mother Name", "Mother Mobile"]
        for col in required_cols:
            if col not in df.columns:
                raise HTTPException(status_code=400, detail=f"Missing required column: {col}")
                
        imported_count = 0
        for index, row in df.iterrows():
            adm_num = str(row["Admission Number"]).strip()
            # Skip if student already exists
            existing = db.query(db_crud.Student).filter(db_crud.Student.admission_number == adm_num).first()
            if existing:
                continue
                
            # Create Parent
            db_parent = db_crud.Parent(
                father_name=str(row["Father Name"]).strip(),
                father_mobile=str(row["Father Mobile"]).strip(),
                mother_name=str(row["Mother Name"]).strip(),
                mother_mobile=str(row["Mother Mobile"]).strip()
            )
            db.add(db_parent)
            db.commit()
            db.refresh(db_parent)
            
            # RFID card handling if column exists and is not empty
            rfid_card_id = None
            if "RFID Card UID" in df.columns and pd.notna(row["RFID Card UID"]):
                uid_str = str(row["RFID Card UID"]).strip()
                if uid_str:
                    rfid_card = db.query(db_crud.RfidCard).filter(db_crud.RfidCard.uid == uid_str).first()
                    if not rfid_card:
                        rfid_card = db_crud.RfidCard(uid=uid_str, status="active")
                        db.add(rfid_card)
                        db.commit()
                        db.refresh(rfid_card)
                    rfid_card_id = rfid_card.id
                    
            # Create Student
            db_student = db_crud.Student(
                admission_number=adm_num,
                roll_number=str(row["Roll Number"]).strip() if "Roll Number" in df.columns and pd.notna(row["Roll Number"]) else None,
                name=str(row["Name"]).strip(),
                class_name=str(row["Class"]).strip(),
                section=str(row["Section"]).strip(),
                gender=str(row["Gender"]).strip() if "Gender" in df.columns and pd.notna(row["Gender"]) else None,
                dob=str(row["DOB"]).strip() if "DOB" in df.columns and pd.notna(row["DOB"]) else None,
                address=str(row["Address"]).strip() if "Address" in df.columns and pd.notna(row["Address"]) else None,
                parent_id=db_parent.id,
                rfid_card_id=rfid_card_id,
                status="active"
            )
            db.add(db_student)
            db.commit()
            imported_count += 1
            
        db_crud.log_audit(db, user_id=current_user.id, action="IMPORT_STUDENTS", details=f"Imported {imported_count} students from Excel")
        return {"message": f"Successfully imported {imported_count} students"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error reading excel: {str(e)}")
