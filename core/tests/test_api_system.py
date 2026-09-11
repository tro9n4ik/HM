import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine, SessionLocal, get_db
from app.models.user import User
from app.models.plugin import Plugin, PluginConfig
from app.models.system import SystemSetting, ActivityLog
from app.api.deps import get_current_user

def override_get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(autouse=True)
def run_around_tests():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    p = Plugin(id="test_plugin", name="test", version="1.0", path="/tmp")
    db.add(p)
    c = PluginConfig(plugin_id="test_plugin", key="TEST_KEY", value="val", is_secret=False)
    db.add(c)
    db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def auth_client():
    app.dependency_overrides[get_current_user] = lambda: {"username": "admin"}
    yield client
    app.dependency_overrides.pop(get_current_user, None)

@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_get_and_update_settings(auth_client):
    response = auth_client.get("/api/system/settings")
    assert response.status_code == 200
    assert response.json() == {}

    response = auth_client.put("/api/system/settings", json={"settings": {"pip_index_url": "http://mirror"}})
    assert response.status_code == 200

    response = auth_client.get("/api/system/settings")
    assert response.status_code == 200
    assert response.json() == {"pip_index_url": "http://mirror"}

def test_backup_restore(auth_client):
    response = auth_client.post("/api/system/backup")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"

    backup_data = response.json()
    assert len(backup_data["configs"]) == 1
    assert backup_data["configs"][0]["key"] == "TEST_KEY"

    # Test Restore
    backup_data["configs"][0]["value"] = "new_val"
    import json
    import tempfile
    import os
    tmp = os.path.join(tempfile.gettempdir(), "test_rest.json")
    with open(tmp, "w") as f:
        json.dump(backup_data, f)

    with open(tmp, "rb") as f:
        response = auth_client.post("/api/system/restore", files={"file": ("hm_backup.json", f, "application/json")})
        assert response.status_code == 200
        assert response.json()["status"] == "restored"

    db = SessionLocal()
    val = db.query(PluginConfig).filter_by(key="TEST_KEY").first().value
    assert val == "new_val"
    db.close()

def test_system_info(auth_client):
    response = auth_client.get("/api/system/info")
    assert response.status_code == 200
    assert "os" in response.json()
    assert response.json()["plugins_count"] == 1

def test_system_stats_unauthorized():
    response = client.get("/api/system/stats")
    assert response.status_code == 401

def test_system_stats(auth_client):
    response = auth_client.get("/api/system/stats")
    assert response.status_code == 200
    data = response.json()
    assert "cpu" in data
    assert "percent" in data["cpu"]
    assert "load" in data["cpu"]
    assert "memory" in data
    assert "used" in data["memory"]
    assert "total" in data["memory"]
    assert "storage" in data
    assert "percent" in data["storage"]

def test_system_health(auth_client, db_session):
    p1 = Plugin(id="1", name="p1", version="1.0", status="running", port=8001, path="/tmp/p1", autostart=False)
    p2 = Plugin(id="2", name="p2", version="1.0", status="degraded", port=8002, path="/tmp/p2", autostart=False)
    db_session.add_all([p1, p2])
    db_session.commit()

    response = auth_client.get("/api/system/health")
    assert response.status_code == 200
    checks = response.json()
    assert len(checks) >= 3 # DB + 3 plugins (1 from setup + 2 here)

    db_check = next(c for c in checks if c["name"] == "Database")
    assert db_check["status"] == "ok"
    assert db_check["message"] == "connected"

    p1_check = next(c for c in checks if c["name"] == "Plugin: p1")
    assert p1_check["status"] == "ok"
    assert p1_check["message"] == "running"

    p2_check = next(c for c in checks if c["name"] == "Plugin: p2")
    assert p2_check["status"] == "error"
    assert p2_check["message"] == "degraded"

def test_system_activity(auth_client, db_session):
    log1 = ActivityLog(source="test", message="msg 1")
    log2 = ActivityLog(source="test2", message="msg 2")
    db_session.add_all([log1, log2])
    db_session.commit()

    response = auth_client.get("/api/system/activity?limit=1")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["message"] == "msg 2" # Descending order
    assert "time" in data[0]
