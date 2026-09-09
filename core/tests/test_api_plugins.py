import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine, SessionLocal, get_db
from app.models.plugin import Plugin, PluginConfig
from app.models.user import User
from app.api.deps import get_current_user

SessionLocal2 = SessionLocal

def override_get_db():
    db = SessionLocal2()
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
    db = SessionLocal2()
    p = Plugin(id="plugin1", name="example", version="1.0", status="running", port=8100, path="/tmp")
    db.add(p)
    c = PluginConfig(plugin_id="plugin1", key="API_KEY", value="secret_value", is_secret=True)
    c2 = PluginConfig(plugin_id="plugin1", key="DEBUG", value="True", is_secret=False)
    db.add(c)
    db.add(c2)
    db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)

def test_list_plugins():
    response = client.get("/api/plugins")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "example"

def test_get_config():
    response = client.get("/api/plugins/plugin1/config")
    assert response.status_code == 200
    data = response.json()
    assert data["API_KEY"] == "***" # Should be masked
    assert data["DEBUG"] == "True"

def test_update_config():
    response = client.put("/api/plugins/plugin1/config", json={"config": {"DEBUG": "False", "API_KEY": "***", "NEW_KEY": "test"}})
    assert response.status_code == 200

    # Check that it updated in DB
    db = SessionLocal2()
    configs = db.query(PluginConfig).filter_by(plugin_id="plugin1").all()
    config_dict = {c.key: c.value for c in configs}
    assert config_dict["DEBUG"] == "False"
    assert config_dict["API_KEY"] == "secret_value" # Should not be overwritten if sent as ***
    assert config_dict["NEW_KEY"] == "test"
    db.close()

def test_plugin_actions(mocker):
    # Mock plugin manager calls
    mocker.patch('app.services.plugin_manager.PluginManager.start_plugin', return_value=True)
    mocker.patch('app.services.plugin_manager.PluginManager.stop_plugin', return_value=True)

    response = client.post("/api/plugins/plugin1/start")
    assert response.status_code == 200

    response = client.post("/api/plugins/plugin1/stop")
    assert response.status_code == 200

    response = client.post("/api/plugins/plugin1/restart")
    assert response.status_code == 200
