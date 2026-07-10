from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Any, List, Optional, Dict

from app.core.database import get_db
from app.crud import db_crud
from app.schemas.schemas import DeviceOut, DeviceRegisterRequest, DeviceHeartbeatRequest, DeviceLogRequest, UserOut
from app.api.auth import get_current_active_user, check_role
from app.core.websockets import manager

router = APIRouter()

@router.get("/", response_model=List[DeviceOut])
def read_devices(
    db: Session = Depends(get_db),
    current_user: UserOut = Depends(get_current_active_user)
) -> Any:
    # Auto mark old devices offline before fetching
    heartbeat_cutoff = datetime.utcnow() - timedelta(minutes=2)
    db.query(db_crud.Device).filter(db_crud.Device.last_seen < heartbeat_cutoff, db_crud.Device.status == "online").update({"status": "offline", "current_status_message": "Offline"})
    db.commit()
    return db.query(db_crud.Device).all()

@router.post("/register")
async def register_device(
    req: DeviceRegisterRequest,
    db: Session = Depends(get_db)
):
    device = db_crud.register_device(db, req=req)
    
    # Broadcast status change
    await manager.broadcast({
        "event": "device_status_changed",
        "device_id": device.device_id,
        "name": device.name,
        "status": "online",
        "message": "Device Registered / Reconnected"
    })
    return {"status": "success", "message": f"Device {device.name} registered successfully."}

@router.post("/heartbeat")
async def device_heartbeat(
    req: DeviceHeartbeatRequest,
    db: Session = Depends(get_db)
):
    device = db_crud.update_device_heartbeat(db, req=req)
    if not device:
        # Create offline/unknown register notice
        raise HTTPException(status_code=404, detail="Device not registered. Please register first.")
        
    # Broadcast heartbeat update to frontend
    await manager.broadcast({
        "event": "device_status_changed",
        "device_id": device.device_id,
        "name": device.name,
        "status": "online",
        "wifi_signal": device.wifi_signal,
        "battery_status": device.battery_status,
        "sim_network": device.sim_network,
        "current_status_message": device.current_status_message,
        "last_seen": device.last_seen.isoformat()
    })
    return {"status": "success"}

@router.post("/log")
def log_device_event(
    req: DeviceLogRequest,
    db: Session = Depends(get_db)
):
    # Log diagnostic message as an audit log or standard database notification if it's an error
    log_msg = f"Device [{req.device_id}] [{req.log_level}]: {req.message}"
    db_crud.log_audit(db, user_id=None, action="DEVICE_LOG", details=log_msg)
    
    if req.log_level.upper() in ["ERROR", "CRITICAL"]:
        db_crud.create_notification(db, notif_type="rfid_error", message=log_msg)
        
    return {"status": "success"}

@router.post("/restart/{device_id}")
async def restart_device(
    device_id: str,
    db: Session = Depends(get_db),
    current_user: UserOut = Depends(check_role(["Super Admin", "School Admin"]))
):
    device = db.query(db_crud.Device).filter(db_crud.Device.device_id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
        
    # Send restart command via websocket
    await manager.broadcast({
        "event": "device_command",
        "device_id": device_id,
        "command": "restart"
    })
    
    db_crud.log_audit(db, user_id=current_user.id, action="DEVICE_RESTART", details=f"Sent restart command to Device: {device.name} ({device_id})")
    return {"message": f"Restart command sent to device {device.name}."}

@router.post("/ota/{device_id}")
async def trigger_ota(
    device_id: str,
    db: Session = Depends(get_db),
    current_user: UserOut = Depends(check_role(["Super Admin"]))
):
    device = db.query(db_crud.Device).filter(db_crud.Device.device_id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
        
    # Send OTA command via websocket
    await manager.broadcast({
        "event": "device_command",
        "device_id": device_id,
        "command": "ota_update"
    })
    
    db_crud.log_audit(db, user_id=current_user.id, action="DEVICE_OTA", details=f"Triggered OTA update placeholder for Device: {device.name}")
    return {"message": f"OTA update instruction transmitted to device {device.name}."}

@router.get("/status")
def get_all_device_status(
    db: Session = Depends(get_db),
    current_user: UserOut = Depends(get_current_active_user)
):
    # Returns online/offline counts and full list
    devices = db.query(db_crud.Device).all()
    online = sum(1 for d in devices if d.status == "online")
    offline = len(devices) - online
    return {
        "online_count": online,
        "offline_count": offline,
        "devices": devices
    }
