import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine, SessionLocal, get_db
from app.models.plugin import Plugin
from app.models.user import User
from app.api.deps import get_current_user
import os

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
    os.environ["SECRET_KEY"] = "test-secret"
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    p = Plugin(name="example", version="1.0", status="running", port=9999, path="/tmp")
    db.add(p)
    p2 = Plugin(name="stopped_plugin", version="1.0", status="stopped", port=9998, path="/tmp")
    db.add(p2)
    db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)

def test_proxy_stopped_plugin():
    response = client.get("/plugins/stopped_plugin/test")
    assert response.status_code == 502

def test_proxy_not_found():
    response = client.get("/plugins/unknown_plugin/test")
    assert response.status_code == 404

def test_proxy_unauthorized():
    app.dependency_overrides.pop(get_current_user, None)

    response = client.get("/plugins/example/test")
    assert response.status_code == 401

    app.dependency_overrides[get_current_user] = override_get_current_user

def test_proxy_websocket_unauthorized():
    from starlette.websockets import WebSocketDisconnect
    app.dependency_overrides.pop(get_current_user, None)

    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect("/plugins/example/test"):
            pass

    assert exc_info.value.code == 1008

    app.dependency_overrides[get_current_user] = override_get_current_user
