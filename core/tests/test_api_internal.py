import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.plugin import Plugin
from app.database import Base, engine, SessionLocal
import json

# Ensure request.client.host is overridden for TestClient
# TestClient defaults to "testclient"
from app.api.internal import verify_internal

app.dependency_overrides[verify_internal] = lambda: None

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    # Add a test plugin
    p = Plugin(name="test_plugin", version="1.0", path="/tmp", port=8001, manifest='{"name": "test_plugin", "config_schema": {}}')
    db.add(p)
    db.commit()
    yield
    db.close()
    Base.metadata.drop_all(bind=engine)

def test_list_internal_plugins():
    response = client.get("/api/internal/plugins")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1

    # Test plugin exists in response
    test_plugin = next((p for p in data if p["name"] == "test_plugin"), None)
    assert test_plugin is not None
    assert test_plugin["port"] == 8001
    assert test_plugin["url"] == "http://127.0.0.1:8001"
    assert "config_schema" in test_plugin["manifest"]
