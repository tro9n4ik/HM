import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine, SessionLocal, get_db
from app.models.user import User
from app.models.system import SystemSetting
from app.api.deps import get_current_user

def override_get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def override_get_current_user():
    return User(username="admin")

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user
client = TestClient(app)

@pytest.fixture(autouse=True)
def run_around_tests():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_get_and_update_settings():
    response = client.get("/api/system/settings")
    assert response.status_code == 200
    assert response.json() == {}

    response = client.put("/api/system/settings", json={"settings": {"pip_index_url": "http://mirror"}})
    assert response.status_code == 200

    response = client.get("/api/system/settings")
    assert response.status_code == 200
    assert response.json() == {"pip_index_url": "http://mirror"}

def test_backup_restore():
    response = client.post("/api/system/backup")
    assert response.status_code == 200
    assert response.json()["status"] == "backup_created"

    response = client.post("/api/system/restore")
    assert response.status_code == 200
    assert response.json()["status"] == "restored"

def test_system_info():
    response = client.get("/api/system/info")
    assert response.status_code == 200
    assert "os" in response.json()
    assert "plugins_count" in response.json()
