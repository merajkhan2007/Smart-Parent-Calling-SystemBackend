from fastapi import FastAPI, Depends, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import uvicorn
import json

from app.core.config import settings
from app.core.database import engine, get_db, Base
from app.core.websockets import manager
from app.crud import db_crud
from app.api import auth, students, parents, rfid, devices, calls, reports, settings as settings_api, notifications

# Initialize tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Smart Parent Calling System API with ESP32 Hardware Integration",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Set CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount core routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["Authentication"])
app.include_router(students.router, prefix=f"{settings.API_V1_STR}/students", tags=["Students"])
app.include_router(parents.router, prefix=f"{settings.API_V1_STR}/parents", tags=["Parents"])
app.include_router(rfid.router, prefix=f"{settings.API_V1_STR}/rfid", tags=["RFID"])
app.include_router(devices.router, prefix=f"{settings.API_V1_STR}/device", tags=["ESP32 Devices"])
app.include_router(devices.router, prefix=f"{settings.API_V1_STR}/devices", tags=["ESP32 Devices"]) # alternative plural route
app.include_router(calls.router, prefix=f"{settings.API_V1_STR}/call", tags=["Calls"])
app.include_router(reports.router, prefix=f"{settings.API_V1_STR}/reports", tags=["Reports"])
app.include_router(settings_api.router, prefix=f"{settings.API_V1_STR}/settings", tags=["Settings"])
app.include_router(notifications.router, prefix=f"{settings.API_V1_STR}/notifications", tags=["Notifications"])

# --- EXACT ESP32 REST API MAPPINGS ---

@app.get("/api/student/{rfid}")
def get_student_by_rfid_card(rfid: str, db: Session = Depends(get_db)):
    student = db_crud.get_student_by_rfid(db, rfid_uid=rfid)
    if not student:
        raise HTTPException(status_code=404, detail="Student not registered or assigned to this RFID")
    if student.status == "blocked":
        raise HTTPException(status_code=403, detail="Student is blocked")
    return {
        "status": "success",
        "student_id": student.id,
        "student_name": student.name,
        "father_name": student.parent.father_name if student.parent else "",
        "father_mobile": student.parent.father_mobile if student.parent else "",
        "mother_name": student.parent.mother_name if student.parent else "",
        "mother_mobile": student.parent.mother_mobile if student.parent else ""
    }

@app.get("/api/parent-number/{student_id}/{type}")
def get_parent_number_direct(student_id: int, type: str, db: Session = Depends(get_db)):
    student = db.query(db_crud.Student).filter(db_crud.Student.id == student_id).first()
    if not student or not student.parent:
        raise HTTPException(status_code=404, detail="Student parent contact details not found")
        
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
        raise HTTPException(status_code=404, detail=f"Phone number not set for {type}")
        
    return {
        "student_id": student_id,
        "parent_type": type,
        "parent_name": name,
        "phone_number": num
    }

# --- REAL-TIME WEBSOCKET ---
@app.websocket("/api/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Receive keep-alive signals or requests from client
            data = await websocket.receive_text()
            # Parse if needed
            message = json.loads(data)
            # Standard ping pong response to keep socket healthy
            if message.get("type") == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)

# Auto seed database on startup
@app.on_event("startup")
def startup_event():
    db = next(get_db())
    # Create default roles
    roles = ["Super Admin", "School Admin", "Teacher"]
    for role_name in roles:
        role = db.query(db_crud.Role).filter(db_crud.Role.name == role_name).first()
        if not role:
            role = db_crud.Role(name=role_name, description=f"{role_name} privileges")
            db.add(role)
            db.commit()
            
    # Create default super admin
    super_admin_role = db.query(db_crud.Role).filter(db_crud.Role.name == "Super Admin").first()
    admin_user = db.query(db_crud.User).filter(db_crud.User.email == "admin@spcs.com").first()
    if not admin_user and super_admin_role:
        db_crud.create_user(
            db,
            db_crud.UserCreate(
                email="admin@spcs.com",
                password="Admin@123",
                full_name="SPCS Super Admin",
                role_id=super_admin_role.id
            )
        )
    db.close()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
