from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_
from datetime import datetime, date, timedelta
from typing import List, Optional, Tuple, Dict, Any

from app.models.database_models import (
    School, User, Role, Permission, Student, Parent, RfidCard, Device, CallLog, Attendance, Setting, Notification, AuditLog
)
from app.schemas.schemas import StudentCreate, StudentUpdate, UserCreate, UserUpdate, ParentCreate, DeviceRegisterRequest, DeviceHeartbeatRequest, DeviceUpdate
from app.core.security import get_password_hash

# --- SCHOOL CRUD ---
def get_school(db: Session, school_id: int) -> Optional[School]:
    return db.query(School).filter(School.id == school_id).first()

def get_school_by_name(db: Session, name: str) -> Optional[School]:
    return db.query(School).filter(School.name == name).first()

def get_schools(db: Session) -> List[School]:
    return db.query(School).all()

def create_school(db: Session, school_name: str, logo_url: str = None) -> School:
    db_school = School(name=school_name, logo_url=logo_url)
    db.add(db_school)
    db.commit()
    db.refresh(db_school)
    
    # Initialize default settings for the school
    db_settings = Setting(
        school_id=db_school.id,
        school_name=school_name,
        logo_url=logo_url,
        working_hours_start="08:00",
        working_hours_end="16:00",
        max_calls_per_day=3,
        max_call_duration=180,
        emergency_contact="+1234567890",
        allowed_calling_time_start="08:00",
        allowed_calling_time_end="16:00"
    )
    db.add(db_settings)
    db.commit()
    return db_school

def delete_school(db: Session, school_id: int) -> bool:
    db_school = db.query(School).filter(School.id == school_id).first()
    if not db_school:
        return False
    db.delete(db_school)
    db.commit()
    return True

# --- AUTH & USER CRUD ---
def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()

def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()

def create_user(db: Session, user: UserCreate) -> User:
    hashed_pwd = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        hashed_password=hashed_pwd,
        full_name=user.full_name,
        role_id=user.role_id,
        school_id=user.school_id,
        is_active=True
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_users(db: Session, school_id: Optional[int] = None) -> List[User]:
    q = db.query(User)
    if school_id is not None:
        q = q.filter(User.school_id == school_id)
    return q.all()

def update_user(db: Session, db_user: User, user_in: UserUpdate) -> User:
    update_data = user_in.model_dump(exclude_unset=True)
    if "password" in update_data:
        password = update_data.pop("password")
        if password:
            db_user.hashed_password = get_password_hash(password)
            
    for field, val in update_data.items():
        setattr(db_user, field, val)
        
    db.commit()
    db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id: int) -> bool:
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        return False
    db.delete(db_user)
    db.commit()
    return True

# --- STUDENT CRUD ---
def get_student(db: Session, student_id: int, school_id: Optional[int] = None) -> Optional[Student]:
    q = db.query(Student).filter(Student.id == student_id)
    if school_id is not None:
        q = q.filter(Student.school_id == school_id)
    return q.first()

def get_student_by_rfid(db: Session, rfid_uid: str) -> Optional[Student]:
    # Hardware checks: can search student globally (since device knows school_id)
    return db.query(Student).join(RfidCard).filter(RfidCard.uid == rfid_uid).first()

def search_students(
    db: Session,
    query: Optional[str] = None,
    class_name: Optional[str] = None,
    section: Optional[str] = None,
    status: Optional[str] = None,
    school_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100
) -> Tuple[List[Student], int]:
    db_query = db.query(Student)
    if school_id is not None:
        db_query = db_query.filter(Student.school_id == school_id)
    
    if query:
        search_filter = or_(
            Student.name.ilike(f"%{query}%"),
            Student.admission_number.ilike(f"%{query}%"),
            Student.roll_number.ilike(f"%{query}%")
        )
        # Check if query matches parent father/mother name or mobile
        parent_query = db.query(Parent.id).filter(
            or_(
                Parent.father_name.ilike(f"%{query}%"),
                Parent.mother_name.ilike(f"%{query}%"),
                Parent.father_mobile.ilike(f"%{query}%"),
                Parent.mother_mobile.ilike(f"%{query}%")
            )
        )
        if school_id is not None:
            parent_query = parent_query.filter(Parent.school_id == school_id)
        
        parent_filter = Student.parent_id.in_(parent_query)
        db_query = db_query.filter(or_(search_filter, parent_filter))
        
    if class_name:
        db_query = db_query.filter(Student.class_name == class_name)
    if section:
        db_query = db_query.filter(Student.section == section)
    if status:
        db_query = db_query.filter(Student.status == status)
        
    total = db_query.count()
    results = db_query.offset(skip).limit(limit).all()
    return results, total

def create_student(db: Session, student_in: StudentCreate) -> Student:
    # 1. Create parent
    db_parent = Parent(
        father_name=student_in.parent.father_name,
        father_mobile=student_in.parent.father_mobile,
        mother_name=student_in.parent.mother_name,
        mother_mobile=student_in.parent.mother_mobile,
        guardian_name=student_in.parent.guardian_name,
        guardian_mobile=student_in.parent.guardian_mobile,
        emergency_contact=student_in.parent.emergency_contact,
        school_id=student_in.school_id
    )
    db.add(db_parent)
    db.commit()
    db.refresh(db_parent)
    
    # 2. Check and handle RFID Card
    rfid_card_id = None
    if student_in.rfid_uid:
        # Check if already exists
        rfid_card = db.query(RfidCard).filter(RfidCard.uid == student_in.rfid_uid).first()
        if not rfid_card:
            rfid_card = RfidCard(uid=student_in.rfid_uid, status="active", school_id=student_in.school_id)
            db.add(rfid_card)
            db.commit()
            db.refresh(rfid_card)
        else:
            rfid_card.school_id = student_in.school_id
            db.commit()
        rfid_card_id = rfid_card.id
        
    # 3. Create Student
    db_student = Student(
        admission_number=student_in.admission_number,
        roll_number=student_in.roll_number,
        name=student_in.name,
        class_name=student_in.class_name,
        section=student_in.section,
        gender=student_in.gender,
        dob=student_in.dob,
        address=student_in.address,
        parent_id=db_parent.id,
        rfid_card_id=rfid_card_id,
        status=student_in.status or "active",
        school_id=student_in.school_id
    )
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student

def update_student(db: Session, student_id: int, student_in: StudentUpdate) -> Optional[Student]:
    db_student = db.query(Student).filter(Student.id == student_id).first()
    if not db_student:
        return None
        
    # Update base fields
    update_data = student_in.model_dump(exclude_unset=True)
    
    # Handle RFID updates
    if "rfid_uid" in update_data:
        rfid_uid = update_data.pop("rfid_uid")
        if rfid_uid:
            # Check if this rfid exists
            rfid_card = db.query(RfidCard).filter(RfidCard.uid == rfid_uid).first()
            if not rfid_card:
                rfid_card = RfidCard(uid=rfid_uid, status="active", school_id=db_student.school_id)
                db.add(rfid_card)
                db.commit()
                db.refresh(rfid_card)
            db_student.rfid_card_id = rfid_card.id
        else:
            db_student.rfid_card_id = None
            
    # Handle Parent updates
    if "parent" in update_data:
        parent_data = update_data.pop("parent")
        if parent_data and db_student.parent:
            for k, v in parent_data.items():
                setattr(db_student.parent, k, v)
                
    for field, val in update_data.items():
        setattr(db_student, field, val)
        
    db.commit()
    db.refresh(db_student)
    return db_student

def delete_student(db: Session, student_id: int) -> bool:
    db_student = db.query(Student).filter(Student.id == student_id).first()
    if not db_student:
        return False
    # If deleting student, delete parent record if they have no other student
    parent_id = db_student.parent_id
    db.delete(db_student)
    db.commit()
    
    if parent_id:
        other_students = db.query(Student).filter(Student.parent_id == parent_id).count()
        if other_students == 0:
            db_parent = db.query(Parent).filter(Parent.id == parent_id).first()
            if db_parent:
                db.delete(db_parent)
                db.commit()
    return True

# --- RFID CARD CRUD ---
def get_rfid_card(db: Session, uid: str) -> Optional[RfidCard]:
    return db.query(RfidCard).filter(RfidCard.uid == uid).first()

def get_rfid_cards(db: Session, school_id: Optional[int] = None) -> List[RfidCard]:
    q = db.query(RfidCard)
    if school_id is not None:
        q = q.filter(RfidCard.school_id == school_id)
    return q.all()

def create_rfid_card(db: Session, uid: str, school_id: Optional[int] = None) -> RfidCard:
    db_card = RfidCard(uid=uid, status="active", school_id=school_id)
    db.add(db_card)
    db.commit()
    db.refresh(db_card)
    return db_card

# --- DEVICES CRUD ---
def register_device(db: Session, req: DeviceRegisterRequest) -> Device:
    db_device = db.query(Device).filter(Device.device_id == req.device_id).first()
    if not db_device:
        db_device = Device(
            device_id=req.device_id,
            name=req.name,
            mac_address=req.mac_address,
            ip_address=req.ip_address,
            firmware_version=req.firmware_version,
            location=req.location,
            classroom=req.classroom,
            school_id=req.school_id,
            status="online",
            last_seen=datetime.utcnow()
        )
        db.add(db_device)
    else:
        db_device.name = req.name
        if req.mac_address: db_device.mac_address = req.mac_address
        if req.ip_address: db_device.ip_address = req.ip_address
        if req.firmware_version: db_device.firmware_version = req.firmware_version
        if req.location: db_device.location = req.location
        if req.classroom: db_device.classroom = req.classroom
        if req.school_id is not None: db_device.school_id = req.school_id
        db_device.status = "online"
        db_device.last_seen = datetime.utcnow()
    db.commit()
    db.refresh(db_device)
    return db_device

def update_device_heartbeat(db: Session, req: DeviceHeartbeatRequest) -> Optional[Device]:
    db_device = db.query(Device).filter(Device.device_id == req.device_id).first()
    if not db_device:
        return None
    db_device.last_seen = datetime.utcnow()
    db_device.status = "online"
    if req.battery_status is not None: db_device.battery_status = req.battery_status
    if req.wifi_signal is not None: db_device.wifi_signal = req.wifi_signal
    if req.sim_network is not None: db_device.sim_network = req.sim_network
    if req.current_status_message is not None: db_device.current_status_message = req.current_status_message
    db.commit()
    db.refresh(db_device)
    return db_device

def update_device(db: Session, db_device: Device, device_in: DeviceUpdate) -> Device:
    update_data = device_in.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(db_device, field, val)
    db.commit()
    db.refresh(db_device)
    return db_device

def get_devices(db: Session, school_id: Optional[int] = None) -> List[Device]:
    q = db.query(Device)
    if school_id is not None:
        q = q.filter(Device.school_id == school_id)
    return q.all()

def delete_device(db: Session, device_id: str) -> bool:
    db_device = db.query(Device).filter(Device.device_id == device_id).first()
    if not db_device:
        return False
    db.delete(db_device)
    db.commit()
    return True

# --- CALL ACTIONS CRUD ---
def create_call_log(db: Session, student_id: int, parent_type: str, phone_number: str, device_db_id: Optional[int], school_id: Optional[int] = None) -> CallLog:
    db_call = CallLog(
        student_id=student_id,
        parent_type=parent_type,
        phone_number=phone_number,
        device_id=device_db_id,
        school_id=school_id,
        call_start=datetime.utcnow(),
        status="started"
    )
    db.add(db_call)
    db.commit()
    db.refresh(db_call)
    return db_call

# --- SYSTEM SETTINGS ---
def get_settings(db: Session, school_id: Optional[int] = None) -> Setting:
    q = db.query(Setting)
    if school_id is not None:
        q = q.filter(Setting.school_id == school_id)
    settings = q.first()
    if not settings:
        settings = Setting(school_id=school_id)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings

# --- NOTIFICATIONS CRUD ---
def create_notification(db: Session, notif_type: str, message: str, school_id: Optional[int] = None) -> Notification:
    db_notif = Notification(type=notif_type, message=message, school_id=school_id, is_read=False)
    db.add(db_notif)
    db.commit()
    db.refresh(db_notif)
    return db_notif

def get_notifications(db: Session, school_id: Optional[int] = None) -> List[Notification]:
    q = db.query(Notification)
    if school_id is not None:
        q = q.filter(Notification.school_id == school_id)
    return q.order_by(Notification.created_at.desc()).all()

# --- AUDIT LOGS CRUD ---
def log_audit(db: Session, user_id: Optional[int], action: str, details: str = None):
    db_log = AuditLog(user_id=user_id, action=action, details=details, timestamp=datetime.utcnow())
    db.add(db_log)
    db.commit()

# --- STATISTICS & DASHBOARD DATA ---
def get_dashboard_stats(db: Session, school_id: Optional[int] = None) -> Dict[str, Any]:
    today_start = datetime.combine(date.today(), datetime.min.time())
    
    total_students_query = db.query(Student)
    if school_id is not None:
        total_students_query = total_students_query.filter(Student.school_id == school_id)
    total_students = total_students_query.count()
    
    # Calls today
    today_calls_query = db.query(CallLog).filter(CallLog.call_start >= today_start)
    if school_id is not None:
        today_calls_query = today_calls_query.filter(CallLog.school_id == school_id)
        
    today_calls = today_calls_query.count()
    successful_calls = today_calls_query.filter(CallLog.status == "completed").count()
    rejected_calls = today_calls_query.filter(CallLog.status.in_(["failed", "rejected", "missed"])).count()
    
    # Call duration today
    call_duration_query = db.query(func.sum(CallLog.duration)).filter(
        CallLog.call_start >= today_start, CallLog.status == "completed"
    )
    if school_id is not None:
        call_duration_query = call_duration_query.filter(CallLog.school_id == school_id)
    call_duration_today = call_duration_query.scalar() or 0
    
    # Scans today
    attendance_query = db.query(Attendance).join(Student).filter(Attendance.check_in_time >= today_start)
    if school_id is not None:
        attendance_query = attendance_query.filter(Student.school_id == school_id)
    scans_today = attendance_query.count()
    
    # Devices online/offline
    heartbeat_cutoff = datetime.utcnow() - timedelta(minutes=2)
    device_update_q = db.query(Device).filter(Device.last_seen < heartbeat_cutoff, Device.status == "online")
    if school_id is not None:
        device_update_q = device_update_q.filter(Device.school_id == school_id)
    device_update_q.update({"status": "offline", "current_status_message": "Offline"}, synchronize_session=False)
    db.commit()
    
    online_device_q = db.query(Device).filter(Device.status == "online")
    offline_device_q = db.query(Device).filter(Device.status == "offline")
    if school_id is not None:
        online_device_q = online_device_q.filter(Device.school_id == school_id)
        offline_device_q = offline_device_q.filter(Device.school_id == school_id)
        
    online_devices = online_device_q.count()
    offline_devices = offline_device_q.count()
    
    # Recent Calls (latest 5)
    recent_calls_q = db.query(CallLog).order_by(CallLog.call_start.desc())
    if school_id is not None:
        recent_calls_q = recent_calls_q.filter(CallLog.school_id == school_id)
    recent_calls = recent_calls_q.limit(5).all()
    
    # Timeline details
    timeline = []
    # Fetch today's call logs
    today_logs_q = db.query(CallLog).filter(CallLog.call_start >= today_start).order_by(CallLog.call_start.desc())
    if school_id is not None:
        today_logs_q = today_logs_q.filter(CallLog.school_id == school_id)
    today_logs = today_logs_q.limit(10).all()
    for log in today_logs:
        timeline.append({
            "id": f"call_{log.id}",
            "type": "call",
            "time": log.call_start.strftime("%H:%M"),
            "title": f"Call to {log.parent_type.capitalize()} of {log.student.name}",
            "subtitle": f"Status: {log.status.capitalize()} | Duration: {log.duration}s",
            "tag": log.status
        })
        
    # Fetch today's attendances
    today_scans_q = db.query(Attendance).join(Student).filter(Attendance.check_in_time >= today_start).order_by(Attendance.check_in_time.desc())
    if school_id is not None:
        today_scans_q = today_scans_q.filter(Student.school_id == school_id)
    today_scans = today_scans_q.limit(10).all()
    for scan in today_scans:
        timeline.append({
            "id": f"scan_{scan.id}",
            "type": "scan",
            "time": scan.check_in_time.strftime("%H:%M"),
            "title": f"RFID Scanned - {scan.student.name}",
            "subtitle": f"Class: {scan.student.class_name}-{scan.student.section}",
            "tag": "scanned"
        })
        
    # Sort timeline by time desc
    timeline = sorted(timeline, key=lambda x: x["time"], reverse=True)[:10]
    
    return {
        "total_students": total_students,
        "today_calls": today_calls,
        "successful_calls": successful_calls,
        "rejected_calls": rejected_calls,
        "call_duration_today": int(call_duration_today),
        "rfid_scans_today": scans_today,
        "online_devices": online_devices,
        "offline_devices": offline_devices,
        "activity_timeline": timeline,
        "recent_calls": recent_calls
    }
