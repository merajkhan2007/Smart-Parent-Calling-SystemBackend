from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from typing import Any, Dict, List

from app.core.database import get_db
from app.crud import db_crud
from app.api.auth import get_current_active_user, check_role
from app.schemas.schemas import UserOut, CallStats

router = APIRouter()

@router.get("/call-statistics", response_model=CallStats)
def get_call_statistics(
    db: Session = Depends(get_db),
    current_user: UserOut = Depends(get_current_active_user)
):
    now = datetime.utcnow()
    
    # 1. Daily call logs counts (last 7 days)
    daily_stats = []
    for i in range(6, -1, -1):
        day = now - timedelta(days=i)
        day_str = day.strftime("%b %d")
        start = datetime.combine(day.date(), datetime.min.time())
        end = datetime.combine(day.date(), datetime.max.time())
        count = db.query(db_crud.CallLog).filter(db_crud.CallLog.call_start >= start, db_crud.CallLog.call_start <= end).count()
        daily_stats.append({"label": day_str, "value": count})
        
    # 2. Weekly calls (last 4 weeks)
    weekly_stats = []
    for i in range(3, -1, -1):
        start = now - timedelta(weeks=i+1)
        end = now - timedelta(weeks=i)
        label = f"W-{i+1}"
        count = db.query(db_crud.CallLog).filter(db_crud.CallLog.call_start >= start, db_crud.CallLog.call_start <= end).count()
        weekly_stats.append({"label": label, "value": count})

    # 3. Monthly calls (last 6 months)
    monthly_stats = []
    for i in range(5, -1, -1):
        # basic month check
        first_day_of_month = (now.replace(day=1) - timedelta(days=i*30))
        month_label = first_day_of_month.strftime("%B")
        start = datetime.combine(first_day_of_month.replace(day=1), datetime.min.time())
        # next month start
        if first_day_of_month.month == 12:
            next_m = start.replace(year=start.year + 1, month=1)
        else:
            next_m = start.replace(month=start.month + 1)
        count = db.query(db_crud.CallLog).filter(db_crud.CallLog.call_start >= start, db_crud.CallLog.call_start < next_m).count()
        monthly_stats.append({"label": month_label, "value": count})
        
    # 4. Status distribution
    status_counts = db.query(
        db_crud.CallLog.status, func.count(db_crud.CallLog.id)
    ).group_by(db_crud.CallLog.status).all()
    status_dist = [{"label": s[0], "value": s[1]} for s in status_counts]
    
    # 5. Most active students (top 5)
    active_students_query = db.query(
        db_crud.Student.name, func.count(db_crud.CallLog.id).label("call_count")
    ).join(db_crud.CallLog).group_by(db_crud.Student.id).order_by(desc("call_count")).limit(5).all()
    most_active = [{"student_name": r[0], "calls_count": r[1]} for r in active_students_query]
    
    # 6. Average call duration
    avg_duration = db.query(func.avg(db_crud.CallLog.duration)).filter(db_crud.CallLog.status == "completed").scalar() or 0.0
    
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
    db: Session = Depends(get_db),
    current_user: UserOut = Depends(get_current_active_user)
):
    devices = db.query(db_crud.Device).all()
    results = []
    for d in devices:
        # Calls made by device
        call_count = db.query(db_crud.CallLog).filter(db_crud.CallLog.device_id == d.id).count()
        # Failed calls
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
    db: Session = Depends(get_db),
    current_user: UserOut = Depends(get_current_active_user)
):
    # Ratio of Father vs Mother dials
    father_calls = db.query(db_crud.CallLog).filter(db_crud.CallLog.parent_type == "father").count()
    mother_calls = db.query(db_crud.CallLog).filter(db_crud.CallLog.parent_type == "mother").count()
    guardian_calls = db.query(db_crud.CallLog).filter(db_crud.CallLog.parent_type == "guardian").count()
    
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
