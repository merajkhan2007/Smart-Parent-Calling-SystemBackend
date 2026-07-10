import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import Base, get_db
from app.crud import db_crud

# Create test DB engine
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_spcs.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="module")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    # Seed roles
    roles = ["Super Admin", "School Admin", "Teacher"]
    for role_name in roles:
        role = db.query(db_crud.Role).filter(db_crud.Role.name == role_name).first()
        if not role:
            role = db_crud.Role(name=role_name, description=f"{role_name} privileges")
            db.add(role)
    db.commit()
    
    # Seed admin user
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
    db.commit()
    
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="module")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

def test_login(client):
    response = client.post(
        "/api/auth/login-json",
        json={"email": "admin@spcs.com", "password": "Admin@123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["role"] == "Super Admin"

def test_get_settings_public(client):
    # Register login to get auth token
    login_res = client.post(
        "/api/auth/login-json",
        json={"email": "admin@spcs.com", "password": "Admin@123"}
    )
    token = login_res.json()["access_token"]
    
    response = client.get(
        "/api/settings/",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "school_name" in data

def test_device_registration(client):
    payload = {
        "device_id": "TEST_ESP32_001",
        "name": "Test Classroom Gate",
        "mac_address": "AA:BB:CC:DD:EE:FF",
        "ip_address": "192.168.1.18",
        "firmware_version": "v1.0"
    }
    response = client.post("/api/device/register", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"

def test_device_heartbeat(client):
    # Register first
    client.post("/api/device/register", json={
        "device_id": "TEST_ESP32_001",
        "name": "Test Classroom Gate"
    })
    
    payload = {
        "device_id": "TEST_ESP32_001",
        "battery_status": 85,
        "wifi_signal": -60,
        "sim_network": "T-Mobile",
        "current_status_message": "RFID Waiting"
    }
    response = client.post("/api/device/heartbeat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
