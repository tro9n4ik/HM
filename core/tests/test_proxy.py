import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine, SessionLocal, get_db
from app.models.plugin import Plugin

TestingSessionLocal2 = SessionLocal

def override_get_db():
    db = TestingSessionLocal2()
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
    db = TestingSessionLocal2()
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
