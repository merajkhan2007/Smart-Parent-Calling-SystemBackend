from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Table, Text, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

# Many-to-Many Association Table for Roles and Permissions
role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True)
)

class School(Base):
    __tablename__ = "schools"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    logo_url = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    users = relationship("User", back_populates="school", cascade="all, delete-orphan")
    students = relationship("Student", back_populates="school", cascade="all, delete-orphan")
    parents = relationship("Parent", back_populates="school", cascade="all, delete-orphan")
    rfid_cards = relationship("RfidCard", back_populates="school", cascade="all, delete-orphan")
    devices = relationship("Device", back_populates="school", cascade="all, delete-orphan")
    settings = relationship("Setting", back_populates="school", cascade="all, delete-orphan")
    call_logs = relationship("CallLog", back_populates="school", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="school", cascade="all, delete-orphan")

class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(String(255))
    
    users = relationship("User", back_populates="role")
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")

class Permission(Base):
    __tablename__ = "permissions"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(String(255))
    
    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100))
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    role = relationship("Role", back_populates="users")
    school = relationship("School", back_populates="users")
    teacher = relationship("Teacher", back_populates="user", uselist=False, cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user")

class Teacher(Base):
    __tablename__ = "teachers"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    employee_id = Column(String(50), unique=True, nullable=False)
    class_teacher_of = Column(String(50))  # e.g., "Class 5-A"
    
    user = relationship("User", back_populates="teacher")
    call_logs = relationship("CallLog", back_populates="teacher")

class Parent(Base):
    __tablename__ = "parents"
    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=True)
    father_name = Column(String(100))
    father_mobile = Column(String(20))
    mother_name = Column(String(100))
    mother_mobile = Column(String(20))
    guardian_name = Column(String(100), nullable=True)
    guardian_mobile = Column(String(20), nullable=True)
    emergency_contact = Column(String(20), nullable=True)
    
    school = relationship("School", back_populates="parents")
    students = relationship("Student", back_populates="parent")

class RfidCard(Base):
    __tablename__ = "rfid_cards"
    id = Column(Integer, primary_key=True, index=True)
    uid = Column(String(50), unique=True, nullable=False, index=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=True)
    status = Column(String(20), default="active")  # active, deactivated
    assigned_at = Column(DateTime, default=datetime.utcnow)
    last_scanned_at = Column(DateTime, nullable=True)
    
    school = relationship("School", back_populates="rfid_cards")
    student = relationship("Student", back_populates="rfid_card", uselist=False)

class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=True)
    admission_number = Column(String(50), unique=True, nullable=False, index=True)
    roll_number = Column(String(50))
    name = Column(String(100), nullable=False, index=True)
    class_name = Column(String(50), nullable=False)
    section = Column(String(20), nullable=False)
    gender = Column(String(20))
    dob = Column(String(20))
    address = Column(Text)
    photo_url = Column(String(255), nullable=True)
    parent_id = Column(Integer, ForeignKey("parents.id", ondelete="SET NULL"), nullable=True)
    rfid_card_id = Column(Integer, ForeignKey("rfid_cards.id", ondelete="SET NULL"), nullable=True, unique=True)
    status = Column(String(20), default="active")  # active, blocked, inactive
    created_at = Column(DateTime, default=datetime.utcnow)
    
    school = relationship("School", back_populates="students")
    parent = relationship("Parent", back_populates="students")
    rfid_card = relationship("RfidCard", back_populates="student")
    call_logs = relationship("CallLog", back_populates="student", cascade="all, delete-orphan")
    attendance = relationship("Attendance", back_populates="student", cascade="all, delete-orphan")

class Device(Base):
    __tablename__ = "devices"
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String(100), unique=True, nullable=False, index=True)  # unique ESP32 id
    name = Column(String(100), nullable=False)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="SET NULL"), nullable=True)
    ip_address = Column(String(50))
    mac_address = Column(String(50))
    location = Column(String(100))
    classroom = Column(String(50))
    firmware_version = Column(String(20))
    battery_status = Column(Integer, nullable=True)  # percentage
    wifi_signal = Column(Integer, nullable=True)     # RSSI dBm
    sim_network = Column(String(50), nullable=True)  # Carrier/signal strength
    last_seen = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default="offline")   # online, offline
    current_status_message = Column(String(100), default="RFID Waiting") # RFID Waiting, Card Scanned, Calling, Connected, Call Ended, Offline
    
    school = relationship("School", back_populates="devices")
    call_logs = relationship("CallLog", back_populates="device")

class CallLog(Base):
    __tablename__ = "call_logs"
    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    parent_type = Column(String(20), nullable=False)  # father, mother, guardian
    phone_number = Column(String(20), nullable=False)
    teacher_id = Column(Integer, ForeignKey("teachers.id", ondelete="SET NULL"), nullable=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="SET NULL"), nullable=True)
    call_start = Column(DateTime, default=datetime.utcnow)
    call_end = Column(DateTime, nullable=True)
    duration = Column(Integer, default=0)  # in seconds
    status = Column(String(20), default="started")  # started, connected, completed, failed, rejected, missed
    reason = Column(String(255), nullable=True)    # low_signal, no_answer, hung_up, busy, error
    
    school = relationship("School", back_populates="call_logs")
    student = relationship("Student", back_populates="call_logs")
    teacher = relationship("Teacher", back_populates="call_logs")
    device = relationship("Device", back_populates="call_logs")

class Attendance(Base):
    __tablename__ = "attendance"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    date = Column(String(20), nullable=False)  # YYYY-MM-DD
    status = Column(String(20), default="present")  # present, absent, late
    check_in_time = Column(DateTime, default=datetime.utcnow)
    scan_id = Column(Integer, nullable=True) # refers to scan event log or RFID card ID
    
    student = relationship("Student", back_populates="attendance")

class Setting(Base):
    __tablename__ = "settings"
    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=True, unique=True)
    school_name = Column(String(255), default="Smart Parent Calling School")
    logo_url = Column(String(255), nullable=True)
    working_hours_start = Column(String(20), default="08:00")
    working_hours_end = Column(String(20), default="16:00")
    max_calls_per_day = Column(Integer, default=3)
    max_call_duration = Column(Integer, default=180)  # in seconds
    emergency_contact = Column(String(20), default="+1234567890")
    allowed_calling_time_start = Column(String(20), default="08:00")
    allowed_calling_time_end = Column(String(20), default="16:00")

    school = relationship("School", back_populates="settings")

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=True)
    type = Column(String(50), nullable=False)  # call_failed, sim_balance_low, device_offline, rfid_error, student_blocked
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    school = relationship("School", back_populates="notifications")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(100), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    details = Column(Text, nullable=True)
    
    user = relationship("User", back_populates="audit_logs")
