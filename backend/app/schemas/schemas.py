from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# --- SCHOOL SCHEMAS ---
class SchoolCreate(BaseModel):
    name: str
    logo_url: Optional[str] = None

class SchoolOut(BaseModel):
    id: int
    name: str
    logo_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# --- AUTH SCHEMAS ---
class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    remember_me: Optional[bool] = False

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    role: str
    email: str
    name: str
    school_id: Optional[int] = None

class TokenPayload(BaseModel):
    sub: Optional[str] = None
    type: Optional[str] = None

# --- ROLE & PERMISSION ---
class PermissionOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True

class RoleOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    permissions: List[PermissionOut] = []

    class Config:
        from_attributes = True

# --- USER SCHEMAS ---
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    is_active: Optional[bool] = True
    school_id: Optional[int] = None

class UserCreate(UserBase):
    password: str
    role_id: int

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    role_id: Optional[int] = None
    school_id: Optional[int] = None
    is_active: Optional[bool] = None

class UserOut(UserBase):
    id: int
    role_id: int
    role: Optional[RoleOut] = None
    created_at: datetime

    class Config:
        from_attributes = True

# --- PARENT SCHEMAS ---
class ParentBase(BaseModel):
    father_name: str
    father_mobile: str
    mother_name: str
    mother_mobile: str
    guardian_name: Optional[str] = None
    guardian_mobile: Optional[str] = None
    emergency_contact: Optional[str] = None
    school_id: Optional[int] = None

class ParentCreate(ParentBase):
    pass

class ParentUpdate(BaseModel):
    father_name: Optional[str] = None
    father_mobile: Optional[str] = None
    mother_name: Optional[str] = None
    mother_mobile: Optional[str] = None
    guardian_name: Optional[str] = None
    guardian_mobile: Optional[str] = None
    emergency_contact: Optional[str] = None
    school_id: Optional[int] = None

class ParentOut(ParentBase):
    id: int

    class Config:
        from_attributes = True

# --- RFID SCHEMAS ---
class RfidCardBase(BaseModel):
    uid: str
    status: Optional[str] = "active"
    school_id: Optional[int] = None

class RfidCardCreate(RfidCardBase):
    pass

class RfidCardUpdate(BaseModel):
    uid: Optional[str] = None
    status: Optional[str] = None
    school_id: Optional[int] = None

class RfidCardOut(RfidCardBase):
    id: int
    assigned_at: datetime
    last_scanned_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class RfidAssignRequest(BaseModel):
    student_id: int
    rfid_uid: str

# --- STUDENT SCHEMAS ---
class StudentBase(BaseModel):
    admission_number: str
    roll_number: Optional[str] = None
    name: str
    class_name: str
    section: str
    gender: Optional[str] = None
    dob: Optional[str] = None
    address: Optional[str] = None
    status: Optional[str] = "active"
    school_id: Optional[int] = None

class StudentCreate(StudentBase):
    parent: ParentCreate
    rfid_uid: Optional[str] = None

class StudentUpdate(BaseModel):
    admission_number: Optional[str] = None
    roll_number: Optional[str] = None
    name: Optional[str] = None
    class_name: Optional[str] = None
    section: Optional[str] = None
    gender: Optional[str] = None
    dob: Optional[str] = None
    address: Optional[str] = None
    status: Optional[str] = None
    parent: Optional[ParentUpdate] = None
    rfid_uid: Optional[str] = None
    school_id: Optional[int] = None

class StudentOut(StudentBase):
    id: int
    photo_url: Optional[str] = None
    parent_id: Optional[int] = None
    parent: Optional[ParentOut] = None
    rfid_card_id: Optional[int] = None
    rfid_card: Optional[RfidCardOut] = None
    created_at: datetime

    class Config:
        from_attributes = True

# --- DEVICE SCHEMAS ---
class DeviceBase(BaseModel):
    device_id: str
    name: str
    location: Optional[str] = None
    classroom: Optional[str] = None
    school_id: Optional[int] = None

class DeviceCreate(DeviceBase):
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    firmware_version: Optional[str] = None

class DeviceUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    classroom: Optional[str] = None
    firmware_version: Optional[str] = None
    status: Optional[str] = None
    current_status_message: Optional[str] = None
    school_id: Optional[int] = None

class DeviceOut(DeviceBase):
    id: int
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    firmware_version: Optional[str] = None
    battery_status: Optional[int] = None
    wifi_signal: Optional[int] = None
    sim_network: Optional[str] = None
    last_seen: datetime
    status: str
    current_status_message: str

    class Config:
        from_attributes = True

class DeviceRegisterRequest(BaseModel):
    device_id: str
    name: str
    mac_address: Optional[str] = None
    ip_address: Optional[str] = None
    firmware_version: Optional[str] = None
    location: Optional[str] = None
    classroom: Optional[str] = None
    school_id: Optional[int] = None

class DeviceHeartbeatRequest(BaseModel):
    device_id: str
    battery_status: Optional[int] = None
    wifi_signal: Optional[int] = None
    sim_network: Optional[str] = None
    current_status_message: Optional[str] = None

class DeviceLogRequest(BaseModel):
    device_id: str
    log_level: str
    message: str

# --- CALL LOG SCHEMAS ---
class CallLogBase(BaseModel):
    student_id: int
    parent_type: str
    phone_number: str
    device_id: Optional[int] = None
    school_id: Optional[int] = None

class CallLogOut(BaseModel):
    id: int
    student_id: int
    student: Optional[StudentOut] = None
    parent_type: str
    phone_number: str
    teacher_id: Optional[int] = None
    device_id: Optional[int] = None
    device: Optional[DeviceOut] = None
    call_start: datetime
    call_end: Optional[datetime] = None
    duration: int
    status: str
    reason: Optional[str] = None
    school_id: Optional[int] = None

class CallStartRequest(BaseModel):
    rfid_uid: str
    device_id: str
    parent_type: str  # father or mother

class CallConnectedRequest(BaseModel):
    call_id: int

class CallEndRequest(BaseModel):
    call_id: int
    duration: int
    status: str  # completed, failed, rejected
    reason: Optional[str] = None

# --- SETTINGS SCHEMAS ---
class SettingsBase(BaseModel):
    school_name: str
    working_hours_start: str
    working_hours_end: str
    max_calls_per_day: int
    max_call_duration: int
    emergency_contact: str
    allowed_calling_time_start: str
    allowed_calling_time_end: str

class SettingsUpdate(BaseModel):
    school_name: Optional[str] = None
    working_hours_start: Optional[str] = None
    working_hours_end: Optional[str] = None
    max_calls_per_day: Optional[int] = None
    max_call_duration: Optional[int] = None
    emergency_contact: Optional[str] = None
    allowed_calling_time_start: Optional[str] = None
    allowed_calling_time_end: Optional[str] = None

class SettingsOut(SettingsBase):
    id: int
    logo_url: Optional[str] = None
    school_id: Optional[int] = None

    class Config:
        from_attributes = True

# --- NOTIFICATION SCHEMAS ---
class NotificationOut(BaseModel):
    id: int
    type: str
    message: str
    is_read: bool
    created_at: datetime
    school_id: Optional[int] = None

    class Config:
        from_attributes = True

# --- REPORT & STATS SCHEMAS ---
class DashboardStats(BaseModel):
    total_students: int
    today_calls: int
    successful_calls: int
    rejected_calls: int
    call_duration_today: int  # in seconds
    rfid_scans_today: int
    online_devices: int
    offline_devices: int
    activity_timeline: List[Dict[str, Any]]
    recent_calls: List[CallLogOut]

class ChartDataPoint(BaseModel):
    label: str
    value: int

class CallStats(BaseModel):
    daily_calls: List[ChartDataPoint]
    weekly_calls: List[ChartDataPoint]
    monthly_calls: List[ChartDataPoint]
    status_distribution: List[ChartDataPoint]
    most_active_students: List[Dict[str, Any]]
    call_duration_average: float

class StudentListOut(BaseModel):
    students: List[StudentOut]
    total: int
    page: int
    limit: int

    class Config:
        from_attributes = True

class CallLogListOut(BaseModel):
    calls: List[CallLogOut]
    total: int
    page: int
    limit: int

    class Config:
        from_attributes = True
