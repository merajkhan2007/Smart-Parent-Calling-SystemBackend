from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Any, List, Optional, Dict
import json

from app.core.database import get_db
from app.crud import db_crud
from app.schemas.schemas import RfidCardOut, RfidAssignRequest, UserOut, RfidCardUpdate
from app.api.auth import get_current_active_user, check_role
from app.core.websockets import manager

router = APIRouter()

@router.get("/", response_model=List[RfidCardOut])
def read_rfid_cards(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: UserOut = Depends(get_current_active_user)
) -> Any:
    query = db.query(db_crud.RfidCard)
    if status:
        query = query.filter(db_crud.RfidCard.status == status)
    return query.all()

@router.post("/scan")
async def scan_rfid(
    payload: Dict[str, str],  # {"uid": "XYZ", "device_id": "ESP32_A"}
    db: Session = Depends(get_db)
):
    uid = payload.get("uid")
    device_id = payload.get("device_id")
    
    if not uid or not device_id:
        raise HTTPException(status_code=400, detail="Missing uid or device_id")
        
    # 1. Update card scan timestamp
    card = db.query(db_crud.RfidCard).filter(db_crud.RfidCard.uid == uid).first()
    if not card:
        # Save card as unassigned so admin can easily assign it
        card = db_crud.create_rfid_card(db, uid=uid)
        
    card.last_scanned_at = datetime.utcnow()
    db.commit()
    
    # 2. Check if student is mapped
    student = db.query(db_crud.Student).filter(db_crud.Student.rfid_card_id == card.id).first()
    
    # Update device state
    device = db.query(db_crud.Device).filter(db_crud.Device.device_id == device_id).first()
    if device:
        device.last_seen = datetime.utcnow()
        device.status = "online"
        
    if not student:
        # Create RFID error notification
        msg = f"Unknown RFID Card scanned: UID {uid} at Device {device_id}"
        db_crud.create_notification(db, notif_type="rfid_error", message=msg)
        if device:
            device.current_status_message = "RFID Error"
            db.commit()
            
        # Broadcast via WebSockets
        await manager.broadcast({
            "event": "rfid_scanned",
            "status": "error",
            "message": "Student not found for this card",
            "uid": uid,
            "device_id": device_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        raise HTTPException(status_code=404, detail="Student not assigned to this RFID UID")
        
    if student.status == "blocked":
        # Create student blocked notification
        msg = f"Blocked student {student.name} tried to scan RFID card at Device {device_id}"
        db_crud.create_notification(db, notif_type="student_blocked", message=msg)
        if device:
            device.current_status_message = "Student Blocked"
            db.commit()
            
        await manager.broadcast({
            "event": "rfid_scanned",
            "status": "blocked",
            "student_id": student.id,
            "student_name": student.name,
            "uid": uid,
            "device_id": device_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        raise HTTPException(status_code=403, detail="Student is blocked")
        
    # Mark Attendance for today
    today_str = datetime.today().strftime("%Y-%m-%d")
    att = db.query(db_crud.Attendance).filter(
        db_crud.Attendance.student_id == student.id,
        db_crud.Attendance.date == today_str
    ).first()
    
    if not att:
        att = db_crud.Attendance(
            student_id=student.id,
            date=today_str,
            status="present",
            check_in_time=datetime.utcnow(),
            scan_id=card.id
        )
        db.add(att)
        db.commit()
        
    # Set device status to Card Scanned
    if device:
        device.current_status_message = "Card Scanned"
        db.commit()
        
    # Broadcast scan success to Frontend
    scan_event_data = {
        "event": "rfid_scanned",
        "status": "success",
        "student_id": student.id,
        "student_name": student.name,
        "class": f"{student.class_name}-{student.section}",
        "uid": uid,
        "device_id": device_id,
        "father_name": student.parent.father_name if student.parent else "",
        "mother_name": student.parent.mother_name if student.parent else "",
        "timestamp": datetime.utcnow().isoformat()
    }
    await manager.broadcast(scan_event_data)
    
    return {
        "status": "success",
        "student_id": student.id,
        "student_name": student.name,
        "father_name": student.parent.father_name if student.parent else "",
        "father_mobile": student.parent.father_mobile if student.parent else "",
        "mother_name": student.parent.mother_name if student.parent else "",
        "mother_mobile": student.parent.mother_mobile if student.parent else ""
    }

@router.post("/assign")
def assign_rfid(
    req: RfidAssignRequest,
    db: Session = Depends(get_db),
    current_user: UserOut = Depends(check_role(["Super Admin", "School Admin"]))
):
    student = db.query(db_crud.Student).filter(db_crud.Student.id == req.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
        
    # Find or create card
    card = db.query(db_crud.RfidCard).filter(db_crud.RfidCard.uid == req.rfid_uid).first()
    if not card:
        card = db_crud.create_rfid_card(db, uid=req.rfid_uid)
        
    if card.status != "active":
        raise HTTPException(status_code=400, detail="RFID Card is deactivated")
        
    # Check if card is already assigned to someone else
    other_student = db.query(db_crud.Student).filter(db_crud.Student.rfid_card_id == card.id).first()
    if other_student and other_student.id != student.id:
        raise HTTPException(status_code=400, detail=f"RFID Card is already assigned to student {other_student.name}")
        
    student.rfid_card_id = card.id
    db.commit()
    db_crud.log_audit(db, user_id=current_user.id, action="ASSIGN_RFID", details=f"Assigned RFID {req.rfid_uid} to student ID {student.id}")
    return {"message": f"Successfully assigned RFID {req.rfid_uid} to student {student.name}"}

@router.post("/deactivate/{uid}")
def deactivate_rfid(
    uid: str,
    db: Session = Depends(get_db),
    current_user: UserOut = Depends(check_role(["Super Admin", "School Admin"]))
):
    card = db.query(db_crud.RfidCard).filter(db_crud.RfidCard.uid == uid).first()
    if not card:
        raise HTTPException(status_code=404, detail="RFID Card not found")
        
    card.status = "deactivated"
    # Unassign from student
    student = db.query(db_crud.Student).filter(db_crud.Student.rfid_card_id == card.id).first()
    if student:
        student.rfid_card_id = None
        
    db.commit()
    db_crud.log_audit(db, user_id=current_user.id, action="DEACTIVATE_RFID", details=f"Deactivated RFID Card: {uid}")
    return {"message": f"RFID Card {uid} has been deactivated and unassigned"}

@router.get("/scan-history")
def read_scan_history(
    db: Session = Depends(get_db),
    current_user: UserOut = Depends(get_current_active_user)
):
    # Fetch all attendances (which are created by RFID scans)
    history = db.query(db_crud.Attendance).order_by(db_crud.Attendance.check_in_time.desc()).limit(100).all()
    results = []
    for h in history:
        card = db.query(db_crud.RfidCard).filter(db_crud.RfidCard.id == h.scan_id).first() if h.scan_id else None
        results.append({
            "id": h.id,
            "student_name": h.student.name,
            "class_section": f"{h.student.class_name}-{h.student.section}",
            "rfid_uid": card.uid if card else "Unknown",
            "timestamp": h.check_in_time,
            "status": h.status
        })
    return results

@router.put("/{card_id}", response_model=RfidCardOut)
def update_rfid_card(
    card_id: int,
    card_in: RfidCardUpdate,
    db: Session = Depends(get_db),
    current_user: UserOut = Depends(check_role(["Super Admin", "School Admin"]))
) -> Any:
    """
    Update RFID Card parameters (UID or status).
    If status is set to deactivated, unassign from student.
    """
    card = db.query(db_crud.RfidCard).filter(db_crud.RfidCard.id == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="RFID Card not found")
        
    update_data = card_in.model_dump(exclude_unset=True)
    if "uid" in update_data:
        # Check if another card already has this UID
        dup = db.query(db_crud.RfidCard).filter(db_crud.RfidCard.uid == update_data["uid"], db_crud.RfidCard.id != card_id).first()
        if dup:
            raise HTTPException(status_code=400, detail="RFID Card UID already exists")
        card.uid = update_data["uid"]
        
    if "status" in update_data:
        card.status = update_data["status"]
        if update_data["status"] == "deactivated":
            # Unassign from student
            student = db.query(db_crud.Student).filter(db_crud.Student.rfid_card_id == card.id).first()
            if student:
                student.rfid_card_id = None
                
    db.commit()
    db.refresh(card)
    db_crud.log_audit(db, user_id=current_user.id, action="UPDATE_RFID_CARD", details=f"Updated RFID Card ID {card_id}")
    return card

@router.delete("/{card_id}", status_code=status.HTTP_200_OK)
def delete_rfid_card(
    card_id: int,
    db: Session = Depends(get_db),
    current_user: UserOut = Depends(check_role(["Super Admin"]))
) -> Any:
    """
    Delete / deregister an RFID card completely.
    """
    card = db.query(db_crud.RfidCard).filter(db_crud.RfidCard.id == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="RFID Card not found")
        
    # Unassign from student if assigned
    student = db.query(db_crud.Student).filter(db_crud.Student.rfid_card_id == card_id).first()
    if student:
        student.rfid_card_id = None
        
    db.delete(card)
    db.commit()
    db_crud.log_audit(db, user_id=current_user.id, action="DELETE_RFID_CARD", details=f"Deleted RFID Card ID {card_id}")
    return {"message": "RFID Card successfully deleted"}
