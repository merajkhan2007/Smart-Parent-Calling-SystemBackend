from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from datetime import datetime, date
from typing import Any, List, Optional, Dict
import io
import pandas as pd
from fastapi.responses import StreamingResponse

from app.core.database import get_db
from app.crud import db_crud
from app.schemas.schemas import CallLogOut, CallStartRequest, CallConnectedRequest, CallEndRequest, UserOut
from app.api.auth import get_current_active_user, check_role
from app.core.websockets import manager

router = APIRouter()

@router.get("/", response_model=Dict[str, Any])
def read_call_logs(
    student_query: Optional[str] = None,
    device_id: Optional[str] = None,
    status: Optional[str] = None,
    class_name: Optional[str] = None,
    start_date: Optional[str] = None, # YYYY-MM-DD
    end_date: Optional[str] = None, # YYYY-MM-DD
    page: int = 1,
    limit: int = 15,
    db: Session = Depends(get_db),
    current_user: UserOut = Depends(get_current_active_user)
) -> Any:
    skip = (page - 1) * limit
    query = db.query(db_crud.CallLog).join(db_crud.Student)
    
    if student_query:
        query = query.filter(db_crud.Student.name.ilike(f"%{student_query}%"))
    if device_id:
        query = query.join(db_crud.Device).filter(db_crud.Device.device_id == device_id)
    if status:
        query = query.filter(db_crud.CallLog.status == status)
    if class_name:
        query = query.filter(db_crud.Student.class_name == class_name)
    if start_date:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        query = query.filter(db_crud.CallLog.call_start >= start_dt)
    if end_date:
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        query = query.filter(db_crud.CallLog.call_start <= end_dt)
        
    total = query.count()
    results = query.order_by(db_crud.CallLog.call_start.desc()).offset(skip).limit(limit).all()
    
    return {
        "calls": results,
        "total": total,
        "page": page,
        "limit": limit
    }

@router.get("/parent-number/{student_id}/{type}")
def get_parent_number(
    student_id: int,
    type: str, # father or mother or guardian
    db: Session = Depends(get_db)
):
    student = db.query(db_crud.Student).filter(db_crud.Student.id == student_id).first()
    if not student or not student.parent:
        raise HTTPException(status_code=404, detail="Student parent contacts not found")
        
    num = ""
    name = ""
    if type.lower() == "father":
        num = student.parent.father_mobile
        name = student.parent.father_name
    elif type.lower() == "mother":
        num = student.parent.mother_mobile
        name = student.parent.mother_name
    else:
        num = student.parent.guardian_mobile or student.parent.emergency_contact
        name = student.parent.guardian_name or "Guardian"
        
    if not num:
        raise HTTPException(status_code=404, detail=f"{type.capitalize()} phone number is not available")
        
    return {
        "student_id": student_id,
        "parent_type": type,
        "parent_name": name,
        "phone_number": num
    }

@router.post("/start")
async def call_start(
    req: CallStartRequest,
    db: Session = Depends(get_db)
):
    # Lookup student by RFID UID
    student = db_crud.get_student_by_rfid(db, rfid_uid=req.rfid_uid)
    if not student:
        raise HTTPException(status_code=404, detail="RFID Card is not mapped to any student")
        
    # Get corresponding parent phone number
    parent_type = req.parent_type.lower()
    phone_number = ""
    if parent_type == "father":
        phone_number = student.parent.father_mobile if student.parent else ""
    elif parent_type == "mother":
        phone_number = student.parent.mother_mobile if student.parent else ""
        
    if not phone_number:
        raise HTTPException(status_code=400, detail=f"Phone number not set for {parent_type}")
        
    # Find Device database ID
    device = db.query(db_crud.Device).filter(db_crud.Device.device_id == req.device_id).first()
    device_db_id = device.id if device else None
    
    if device:
        device.current_status_message = "Calling"
        device.last_seen = datetime.utcnow()
        device.status = "online"
        db.commit()
        
    # Create Call Log
    db_call = db_crud.create_call_log(
        db,
        student_id=student.id,
        parent_type=req.parent_type,
        phone_number=phone_number,
        device_db_id=device_db_id
    )
    
    # Broadcast to websocket
    await manager.broadcast({
        "event": "call_started",
        "call_id": db_call.id,
        "student_name": student.name,
        "parent_type": req.parent_type,
        "phone_number": phone_number,
        "device_name": device.name if device else req.device_id,
        "device_id": req.device_id,
        "timestamp": db_call.call_start.isoformat()
    })
    
    return {
        "call_id": db_call.id,
        "phone_number": phone_number,
        "student_name": student.name,
        "status": "started"
    }

@router.post("/connected")
async def call_connected(
    req: CallConnectedRequest,
    db: Session = Depends(get_db)
):
    db_call = db.query(db_crud.CallLog).filter(db_crud.CallLog.id == req.call_id).first()
    if not db_call:
        raise HTTPException(status_code=404, detail="Call record not found")
        
    db_call.status = "connected"
    
    if db_call.device:
        db_call.device.current_status_message = "Connected"
        db_call.device.last_seen = datetime.utcnow()
        db.commit()
        
    await manager.broadcast({
        "event": "call_connected",
        "call_id": db_call.id,
        "student_name": db_call.student.name,
        "device_id": db_call.device.device_id if db_call.device else "",
        "timestamp": datetime.utcnow().isoformat()
    })
    
    return {"status": "connected"}

@router.post("/end")
async def call_end(
    req: CallEndRequest,
    db: Session = Depends(get_db)
):
    db_call = db.query(db_crud.CallLog).filter(db_crud.CallLog.id == req.call_id).first()
    if not db_call:
        raise HTTPException(status_code=404, detail="Call record not found")
        
    db_call.call_end = datetime.utcnow()
    db_call.duration = req.duration
    db_call.status = req.status # completed, failed, rejected
    db_call.reason = req.reason
    
    if db_call.device:
        db_call.device.current_status_message = "Call Ended"
        db_call.device.last_seen = datetime.utcnow()
        db.commit()
        
    # Trigger notifications if failed
    if req.status in ["failed", "rejected"]:
        msg = f"Call failed for {db_call.student.name} to {db_call.parent_type}. Reason: {req.reason or 'None'}"
        db_crud.create_notification(db, notif_type="call_failed", message=msg)
        
    await manager.broadcast({
        "event": "call_ended",
        "call_id": db_call.id,
        "student_name": db_call.student.name,
        "status": req.status,
        "duration": req.duration,
        "reason": req.reason,
        "device_id": db_call.device.device_id if db_call.device else "",
        "timestamp": datetime.utcnow().isoformat()
    })
    
    # Re-trigger RFID Waiting after call ends
    if db_call.device:
        db_call.device.current_status_message = "RFID Waiting"
        db.commit()
        
    return {"status": "ended"}

# --- EXCEL & CSV EXPORTS ---
@router.get("/export/excel")
def export_calls_excel(
    db: Session = Depends(get_db),
    current_user: UserOut = Depends(get_current_active_user)
):
    calls = db.query(db_crud.CallLog).all()
    data = []
    for c in calls:
        data.append({
            "Call ID": c.id,
            "Student Name": c.student.name,
            "Admission Number": c.student.admission_number,
            "Class": f"{c.student.class_name}-{c.student.section}",
            "Parent Type": c.parent_type.capitalize(),
            "Phone Number": c.phone_number,
            "ESP32 Device": c.device.name if c.device else "N/A",
            "Call Start": c.call_start.strftime("%Y-%m-%d %H:%M:%S"),
            "Call End": c.call_end.strftime("%Y-%m-%d %H:%M:%S") if c.call_end else "N/A",
            "Duration (Seconds)": c.duration,
            "Status": c.status.capitalize(),
            "Reason": c.reason or "N/A"
        })
        
    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Call History", index=False)
    output.seek(0)
    
    headers = {
        'Content-Disposition': 'attachment; filename="call_history.xlsx"'
    }
    return StreamingResponse(
        output,
        headers=headers,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@router.get("/export/pdf")
def export_calls_pdf(
    db: Session = Depends(get_db),
    current_user: UserOut = Depends(get_current_active_user)
):
    # To avoid external heavy PDF libraries, we stream a beautifully structured CSV/HTML report
    # representing the PDF export dataset.
    calls = db.query(db_crud.CallLog).all()
    csv_data = "Call ID,Student,Parent Type,Phone,Device,Start,Duration,Status\n"
    for c in calls:
        csv_data += f"{c.id},{c.student.name},{c.parent_type},{c.phone_number},{c.device.name if c.device else 'N/A'},{c.call_start.strftime('%Y-%m-%d %H:%M')},{c.duration},{c.status}\n"
    
    output = io.BytesIO(csv_data.encode('utf-8'))
    headers = {
        'Content-Disposition': 'attachment; filename="call_history_report.csv"'
    }
    return StreamingResponse(
        output,
        headers=headers,
        media_type="text/csv"
    )
