from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, or_
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from app.core.database import get_db
from app.crud import db_crud
from app.api.auth import get_current_active_user, check_role
from app.schemas.schemas import UserOut, CallStats

router = APIRouter()

@router.get("/call-statistics", response_model=CallStats)
def get_call_statistics(
    school_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: UserOut = Depends(get_current_active_user)
):
    target_school_id = school_id
    if current_user.role.name != "Super Admin":
        target_school_id = current_user.school_id

    now = datetime.utcnow()
    
    # 1. Daily call logs counts (last 7 days)
    daily_stats = []
    for i in range(6, -1, -1):
        day = now - timedelta(days=i)
        day_str = day.strftime("%b %d")
        start = datetime.combine(day.date(), datetime.min.time())
        end = datetime.combine(day.date(), datetime.max.time())
        
        q = db.query(db_crud.CallLog).filter(db_crud.CallLog.call_start >= start, db_crud.CallLog.call_start <= end)
        if target_school_id is not None:
            q = q.filter(db_crud.CallLog.school_id == target_school_id)
        
        count = q.count()
        daily_stats.append({"label": day_str, "value": count})
        
    # 2. Weekly calls (last 4 weeks)
    weekly_stats = []
    for i in range(3, -1, -1):
        start = now - timedelta(weeks=i+1)
        end = now - timedelta(weeks=i)
        label = f"W-{i+1}"
        
        q = db.query(db_crud.CallLog).filter(db_crud.CallLog.call_start >= start, db_crud.CallLog.call_start <= end)
        if target_school_id is not None:
            q = q.filter(db_crud.CallLog.school_id == target_school_id)
            
        count = q.count()
        weekly_stats.append({"label": label, "value": count})

    # 3. Monthly calls (last 6 months)
    monthly_stats = []
    for i in range(5, -1, -1):
        first_day_of_month = (now.replace(day=1) - timedelta(days=i*30))
        month_label = first_day_of_month.strftime("%B")
        start = datetime.combine(first_day_of_month.replace(day=1), datetime.min.time())
        if first_day_of_month.month == 12:
            next_m = start.replace(year=start.year + 1, month=1)
        else:
            next_m = start.replace(month=start.month + 1)
            
        q = db.query(db_crud.CallLog).filter(db_crud.CallLog.call_start >= start, db_crud.CallLog.call_start < next_m)
        if target_school_id is not None:
            q = q.filter(db_crud.CallLog.school_id == target_school_id)
            
        count = q.count()
        monthly_stats.append({"label": month_label, "value": count})
        
    # 4. Status distribution
    q_status = db.query(db_crud.CallLog.status, func.count(db_crud.CallLog.id))
    if target_school_id is not None:
        q_status = q_status.filter(db_crud.CallLog.school_id == target_school_id)
    status_counts = q_status.group_by(db_crud.CallLog.status).all()
    status_dist = [{"label": s[0], "value": s[1]} for s in status_counts]
    
    # 5. Most active students (top 5)
    q_active = db.query(db_crud.Student.name, func.count(db_crud.CallLog.id).label("call_count")).join(db_crud.CallLog)
    if target_school_id is not None:
        q_active = q_active.filter(db_crud.Student.school_id == target_school_id)
    active_students_query = q_active.group_by(db_crud.Student.id).order_by(desc("call_count")).limit(5).all()
    most_active = [{"student_name": r[0], "calls_count": r[1]} for r in active_students_query]
    
    # 6. Average call duration
    q_duration = db.query(func.avg(db_crud.CallLog.duration)).filter(db_crud.CallLog.status == "completed")
    if target_school_id is not None:
        q_duration = q_duration.filter(db_crud.CallLog.school_id == target_school_id)
    avg_duration = q_duration.scalar() or 0.0
    
    return {
        "daily_calls": daily_stats,
        "weekly_calls": weekly_stats,
        "monthly_calls": monthly_stats,
        "status_distribution": status_dist,
        "most_active_students": most_active,
        "call_duration_average": float(avg_duration)
    }

@router.get("/device-statistics")
def get_device_statistics(
    school_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: UserOut = Depends(get_current_active_user)
):
    target_school_id = school_id
    if current_user.role.name != "Super Admin":
        target_school_id = current_user.school_id

    devices_q = db.query(db_crud.Device)
    if target_school_id is not None:
        devices_q = devices_q.filter(db_crud.Device.school_id == target_school_id)
    devices = devices_q.all()
    
    results = []
    for d in devices:
        call_count = db.query(db_crud.CallLog).filter(db_crud.CallLog.device_id == d.id).count()
        failed_count = db.query(db_crud.CallLog).filter(
            db_crud.CallLog.device_id == d.id, db_crud.CallLog.status.in_(["failed", "rejected"])
        ).count()
        
        results.append({
            "device_id": d.device_id,
            "name": d.name,
            "location": d.location,
            "status": d.status,
            "wifi_signal": d.wifi_signal,
            "battery_status": d.battery_status,
            "sim_network": d.sim_network,
            "total_calls": call_count,
            "failed_calls": failed_count,
            "success_rate": round(((call_count - failed_count) / call_count * 100), 1) if call_count > 0 else 100.0
        })
    return results

@router.get("/parent-contact-statistics")
def get_parent_contact_statistics(
    school_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: UserOut = Depends(get_current_active_user)
):
    target_school_id = school_id
    if current_user.role.name != "Super Admin":
        target_school_id = current_user.school_id

    q_father = db.query(db_crud.CallLog).filter(db_crud.CallLog.parent_type == "father")
    q_mother = db.query(db_crud.CallLog).filter(db_crud.CallLog.parent_type == "mother")
    q_guardian = db.query(db_crud.CallLog).filter(db_crud.CallLog.parent_type == "guardian")
    
    if target_school_id is not None:
        q_father = q_father.filter(db_crud.CallLog.school_id == target_school_id)
        q_mother = q_mother.filter(db_crud.CallLog.school_id == target_school_id)
        q_guardian = q_guardian.filter(db_crud.CallLog.school_id == target_school_id)
        
    father_calls = q_father.count()
    mother_calls = q_mother.count()
    guardian_calls = q_guardian.count()
    
    total = father_calls + mother_calls + guardian_calls
    return {
        "father_calls": father_calls,
        "mother_calls": mother_calls,
        "guardian_calls": guardian_calls,
        "percentages": {
            "father": round((father_calls / total * 100), 1) if total > 0 else 0.0,
            "mother": round((mother_calls / total * 100), 1) if total > 0 else 0.0,
            "guardian": round((guardian_calls / total * 100), 1) if total > 0 else 0.0
        }
    }
