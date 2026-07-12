import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import random

from app.core.database import SessionLocal, Base, engine
from app.models.database_models import (
    School, User, Role, Permission, Student, Parent, RfidCard, Device, CallLog, Attendance, Setting, Notification
)
from app.core.security import get_password_hash

def seed_db():
    print("Seeding multi-tenant database...")
    db = SessionLocal()
    # 0. Recreate tables
    # Terminate other connections to prevent table locks
    try:
        db.execute(text("SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'neondb' AND pid <> pg_backend_pid();"))
        db.commit()
        print("Terminated other connections successfully.")
    except Exception as e:
        print("Could not terminate other connections:", e)

    # Drop existing tables to ensure schema matches the new multi-school structure
    tables_to_drop = [
        "attendance", "call_logs", "notifications", "students", "rfid_cards", 
        "parents", "settings", "teachers", "audit_logs", "users", "role_permissions", 
        "roles", "permissions", "schools"
    ]
    for table in tables_to_drop:
        try:
            db.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE;"))
            db.commit()
        except Exception as e:
            print(f"Failed to drop table {table}:", e)
            db.rollback()

    Base.metadata.create_all(bind=engine)
    
    # 1. Create Schools
    schools = {}
    school_names = ["Oakridge International School", "Pinecrest Academy"]
    for sname in school_names:
        school = School(name=sname, logo_url="/logo.png")
        db.add(school)
        db.commit()
        db.refresh(school)
        schools[sname] = school

    # 2. Create Roles
    role_names = ["Super Admin", "School Admin", "Teacher"]
    roles = {}
    for rname in role_names:
        role = Role(name=rname, description=f"{rname} role privileges")
        db.add(role)
        db.commit()
        db.refresh(role)
        roles[rname] = role
        
    # 3. Create Users
    users_data = [
        # Global Super Admin (no school context)
        {"email": "superadmin@spcs.com", "name": "Global Super Admin", "role": "Super Admin", "pass": "SuperAdmin@123", "school": None},
        # School Admins
        {"email": "admin@spcs.com", "name": "Oakridge Admin", "role": "School Admin", "pass": "Admin@123", "school": "Oakridge International School"},
        {"email": "pinecrestadmin@spcs.com", "name": "Pinecrest Admin", "role": "School Admin", "pass": "Admin@123", "school": "Pinecrest Academy"},
        # Teachers
        {"email": "teacher1@spcs.com", "name": "Sarah Connor", "role": "Teacher", "pass": "Teacher@123", "school": "Oakridge International School"},
        {"email": "teacher2@spcs.com", "name": "John Keating", "role": "Teacher", "pass": "Teacher@123", "school": "Pinecrest Academy"}
    ]
    
    for u in users_data:
        school_id = schools[u["school"]].id if u["school"] else None
        user = User(
            email=u["email"],
            hashed_password=get_password_hash(u["pass"]),
            full_name=u["name"],
            role_id=roles[u["role"]].id,
            school_id=school_id,
            is_active=True
        )
        db.add(user)
        db.commit()
            
    # 4. Create Settings for both schools
    for sname, school in schools.items():
        settings = Setting(
            school_id=school.id,
            school_name=sname,
            logo_url="/logo.png",
            working_hours_start="08:00",
            working_hours_end="16:30",
            max_calls_per_day=3,
            max_call_duration=120,
            emergency_contact="+14155552671" if school.id == 1 else "+15105559872",
            allowed_calling_time_start="08:00",
            allowed_calling_time_end="16:00"
        )
        db.add(settings)
    db.commit()
        
    # 5. Create ESP32 Devices distributed across schools
    devices_data = [
        # Oakridge
        {"device_id": "ESP32_MAIN_GATE", "name": "Oakridge Main Entrance", "loc": "Main Gate", "room": "Foyer", "status": "online", "msg": "RFID Waiting", "signal": -52, "carrier": "T-Mobile LTE", "school": "Oakridge International School"},
        {"device_id": "ESP32_SEC_GATE", "name": "Oakridge Secondary Exit", "loc": "Side Exit", "room": "Security Room", "status": "online", "msg": "RFID Waiting", "signal": -60, "carrier": "Verizon LTE", "school": "Oakridge International School"},
        # Pinecrest
        {"device_id": "ESP32_CLASS_5A", "name": "Pinecrest classroom 5-A", "loc": "Block C Floor 2", "room": "Room 204", "status": "offline", "msg": "Offline", "signal": None, "carrier": None, "school": "Pinecrest Academy"},
        {"device_id": "ESP32_CLASS_6B", "name": "Pinecrest Classroom 6-B", "loc": "Block B Floor 1", "room": "Room 102", "status": "online", "msg": "RFID Waiting", "signal": -45, "carrier": "AT&T LTE", "school": "Pinecrest Academy"}
    ]
    
    device_instances = []
    for d in devices_data:
        school_id = schools[d["school"]].id
        device = Device(
            device_id=d["device_id"],
            name=d["name"],
            location=d["loc"],
            classroom=d["room"],
            school_id=school_id,
            ip_address=f"192.168.1.{random.randint(100, 250)}",
            mac_address=f"24:0A:C4:F3:{random.randint(10,99)}:{random.randint(10,99)}",
            firmware_version="v2.1.4",
            battery_status=random.choice([80, 95, 100, 45]),
            wifi_signal=d["signal"],
            sim_network=d["carrier"],
            status=d["status"],
            current_status_message=d["msg"],
            last_seen=datetime.utcnow() - (timedelta(hours=5) if d["status"] == "offline" else timedelta(seconds=20))
        )
        db.add(device)
        db.commit()
        db.refresh(device)
        device_instances.append(device)
        
    # 6. Create Students/Parents/RFID cards distributed across schools
    students_data = [
        # Oakridge
        {"adm": "ADM2026001", "roll": "10", "name": "Liam Nelson", "cls": "Class 5", "sec": "A", "gen": "Male", "dob": "2015-04-12", "rfid": "RFID_001_ABC", "father": "David Nelson", "father_mob": "+15550100", "mother": "Emily Nelson", "mother_mob": "+15550101", "school": "Oakridge International School"},
        {"adm": "ADM2026002", "roll": "15", "name": "Olivia Smith", "cls": "Class 5", "sec": "A", "gen": "Female", "dob": "2015-09-24", "rfid": "RFID_002_DEF", "father": "Michael Smith", "father_mob": "+15550200", "mother": "Sarah Smith", "mother_mob": "+15550201", "school": "Oakridge International School"},
        {"adm": "ADM2026005", "roll": "07", "name": "Ethan Davis", "cls": "Class 5", "sec": "A", "gen": "Male", "dob": "2015-06-18", "rfid": "RFID_005_MNO", "father": "Charles Davis", "father_mob": "+15550500", "mother": "Patricia Davis", "mother_mob": "+15550501", "status": "blocked", "school": "Oakridge International School"},
        # Pinecrest
        {"adm": "ADM2026003", "roll": "21", "name": "Noah Williams", "cls": "Class 6", "sec": "B", "gen": "Male", "dob": "2014-01-30", "rfid": "RFID_003_GHI", "father": "James Williams", "father_mob": "+15550300", "mother": "Emma Williams", "mother_mob": "+15550301", "school": "Pinecrest Academy"},
        {"adm": "ADM2026004", "roll": "02", "name": "Ava Martinez", "cls": "Class 6", "sec": "B", "gen": "Female", "dob": "2014-11-05", "rfid": "RFID_004_JKL", "father": "Robert Martinez", "father_mob": "+15550400", "mother": "Maria Martinez", "mother_mob": "+15550401", "school": "Pinecrest Academy"}
    ]
    
    student_instances = []
    for s in students_data:
        school_id = schools[s["school"]].id
        
        # Create parent
        parent = Parent(
            father_name=s["father"],
            father_mobile=s["father_mob"],
            mother_name=s["mother"],
            mother_mobile=s["mother_mob"],
            school_id=school_id
        )
        db.add(parent)
        db.commit()
        db.refresh(parent)
        
        # Create RFID Card
        card = RfidCard(
            uid=s["rfid"],
            status="active",
            school_id=school_id,
            last_scanned_at=datetime.utcnow() - timedelta(minutes=random.randint(10, 600))
        )
        db.add(card)
        db.commit()
        db.refresh(card)
        
        # Create Student
        student = Student(
            admission_number=s["adm"],
            roll_number=s["roll"],
            name=s["name"],
            class_name=s["cls"],
            section=s["sec"],
            gender=s["gen"],
            dob=s["dob"],
            address="123 Oakridge Street, California, USA",
            parent_id=parent.id,
            rfid_card_id=card.id,
            status=s.get("status", "active"),
            school_id=school_id
        )
        db.add(student)
        db.commit()
        db.refresh(student)
        student_instances.append(student)
        
    # 7. Create Attendances (Today)
    today_str = datetime.today().strftime("%Y-%m-%d")
    for s in student_instances:
        if s.status != "blocked":
            att = Attendance(
                student_id=s.id,
                date=today_str,
                status="present",
                check_in_time=datetime.utcnow() - timedelta(hours=random.randint(1, 5)),
                scan_id=s.rfid_card_id
            )
            db.add(att)
            db.commit()
                
    # 8. Seed Call Logs (History for charts)
    call_statuses = ["completed", "completed", "completed", "failed", "rejected"]
    call_reasons = {
        "completed": ["hung_up"],
        "failed": ["low_signal", "error"],
        "rejected": ["busy", "no_answer"]
    }
    
    # Create 40 mock calls spanning the last 7 days distributed by school
    for i in range(40):
        student = random.choice(student_instances)
        school_id = student.school_id
        
        # Match device in same school
        matching_devices = [d for d in device_instances if d.school_id == school_id]
        if not matching_devices:
            continue
        device = random.choice(matching_devices)
        
        day_offset = random.randint(0, 6)
        cstart = datetime.utcnow() - timedelta(days=day_offset, hours=random.randint(1, 10), minutes=random.randint(10, 50))
        status = random.choice(call_statuses)
        reason = random.choice(call_reasons[status])
        duration = random.randint(15, 150) if status == "completed" else 0
        parent_type = random.choice(["father", "mother"])
        phone = student.parent.father_mobile if parent_type == "father" else student.parent.mother_mobile
        
        call = CallLog(
            student_id=student.id,
            parent_type=parent_type,
            phone_number=phone,
            device_id=device.id,
            school_id=school_id,
            call_start=cstart,
            call_end=cstart + timedelta(seconds=duration) if status == "completed" else None,
            duration=duration,
            status=status,
            reason=reason
        )
        db.add(call)
        db.commit()
            
    # 9. Seed Notifications
    notifs = [
        {"type": "device_offline", "msg": "Device Oakridge Secondary Exit went offline: connection lost", "school": "Oakridge International School"},
        {"type": "sim_balance_low", "msg": "LTE Module A7672S at Pinecrest Classroom 6-B reports low SIM balance", "school": "Pinecrest Academy"},
        {"type": "call_failed", "msg": "Call to Mother of Liam Nelson failed. Reason: busy", "school": "Oakridge International School"},
        {"type": "rfid_error", "msg": "Unknown RFID card scanned: UID RFID_999_UNK at Pinecrest Classroom 6-B", "school": "Pinecrest Academy"}
    ]
    for n in notifs:
        school_id = schools[n["school"]].id
        notif = Notification(
            type=n["type"],
            message=n["msg"],
            school_id=school_id,
            is_read=False,
            created_at=datetime.utcnow() - timedelta(minutes=random.randint(2, 100))
        )
        db.add(notif)
        db.commit()
            
    print("Database seeding completed successfully with multi-tenant data.")
    db.close()

if __name__ == "__main__":
    seed_db()
