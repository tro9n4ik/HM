from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine, SessionLocal, get_db
import pytest
import os

TestingSessionLocal = SessionLocal

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(autouse=True)
def run_around_tests():
    # Set a dummy secret key for testing
    os.environ["SECRET_KEY"] = "dummy-test-secret"
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_setup_status_initially_required():
    response = client.get("/api/system/setup-status")
    assert response.status_code == 200
    assert response.json()["setup_required"] is True

def test_setup_admin():
    response = client.post("/api/auth/setup", json={"username": "admin", "password": "password123"})
    assert response.status_code == 200

    response2 = client.get("/api/system/setup-status")
    assert response2.json()["setup_required"] is False

def test_setup_already_completed():
    client.post("/api/auth/setup", json={"username": "admin", "password": "password123"})
    response = client.post("/api/auth/setup", json={"username": "admin2", "password": "password123"})
    assert response.status_code == 400

def test_login():
    client.post("/api/auth/setup", json={"username": "admin", "password": "password123"})
    response = client.post("/api/auth/login", json={"username": "admin", "password": "password123"})
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "access_token" in response.cookies
