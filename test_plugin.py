import sys
sys.path.insert(0, "/app/core")
from fastapi.testclient import TestClient
from app.main import app
from app.api.deps import get_current_user
from app.database import Base, engine, SessionLocal, get_db

Base.metadata.create_all(bind=engine)

def override_get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_current_user] = lambda: {"username": "admin"}
app.dependency_overrides[get_db] = override_get_db

import time

with TestClient(app) as client:
    for p in ["home_assistant", "torrents", "example"]:
        with open(f"/app/plugins/{p}.hm", "rb") as f:
            res = client.post("/api/plugins/install", files={"file": (f"{p}.hm", f, "application/zip")})
            plugin_id = res.json().get("id")

        if plugin_id:
            res = client.post(f"/api/plugins/{plugin_id}/start")

            for _ in range(15):
                res = client.get(f"/api/plugins")
                target = next((x for x in res.json() if x["id"] == plugin_id), None)
                if target and target["status"] in ["running", "degraded", "failed"]:
                    print(f"status {p}:", target["status"], target.get("last_error"))
                    break
                time.sleep(1)
