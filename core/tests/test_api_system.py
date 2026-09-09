import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine, SessionLocal, get_db
from app.models.user import User
from app.models.plugin import Plugin, PluginConfig
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
    db = SessionLocal()
    p = Plugin(id="test_plugin", name="test", version="1.0", path="/tmp")
    db.add(p)
    c = PluginConfig(plugin_id="test_plugin", key="TEST_KEY", value="val", is_secret=False)
    db.add(c)
    db.commit()
    db.close()
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
        response = client.post("/api/system/restore", files={"file": ("hm_backup.json", f, "application/json")})
        assert response.status_code == 200
        assert response.json()["status"] == "restored"

    db = SessionLocal()
    val = db.query(PluginConfig).filter_by(key="TEST_KEY").first().value
    assert val == "new_val"
    db.close()

def test_system_info():
    response = client.get("/api/system/info")
    assert response.status_code == 200
    assert "os" in response.json()
    assert response.json()["plugins_count"] == 1
