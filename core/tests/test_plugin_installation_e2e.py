import pytest
import os
import zipfile
import asyncio
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine, SessionLocal
from app.api.deps import get_current_user

# Mock auth
def override_get_current_user():
    return {"username": "admin"}

@pytest.fixture(autouse=True)
def setup_db():
    app.dependency_overrides[get_current_user] = override_get_current_user
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.pop(get_current_user, None)

def create_dummy_plugin_zip(tmp_path):
    plugin_dir = tmp_path / "dummy_plugin"
    plugin_dir.mkdir()

    with open(plugin_dir / "manifest.json", "w") as f:
        f.write('{"name": "dummy_plugin", "version": "1.0", "config_schema": {}}')

    with open(plugin_dir / "requirements.txt", "w") as f:
        f.write('httpx\nfastapi\nuvicorn\n')

    with open(plugin_dir / "main.py", "w") as f:
        f.write('''
import os
from plugin_sdk import PluginApp
app = PluginApp("dummy_plugin")
@app.get("/health")
def health(): return {"status": "ok"}
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=int(os.environ.get("PLUGIN_PORT", 8999)))
''')

    zip_path = tmp_path / "dummy_plugin.hm"
    with zipfile.ZipFile(zip_path, "w") as z:
        z.write(plugin_dir / "manifest.json", arcname="manifest.json")
        z.write(plugin_dir / "main.py", arcname="main.py")
        z.write(plugin_dir / "requirements.txt", arcname="requirements.txt")

    return zip_path

@pytest.mark.asyncio
async def test_plugin_installation_and_startup(tmp_path):
    # Setup dummy zip
    zip_path = create_dummy_plugin_zip(tmp_path)

    with TestClient(app) as client:
        # 1. Install
        with open(zip_path, "rb") as f:
            res = client.post("/api/plugins/install", files={"file": ("dummy_plugin.hm", f, "application/zip")})
        assert res.status_code == 200
        plugin_id = res.json()["id"]

        # 2. Start
        res = client.post(f"/api/plugins/{plugin_id}/start")
        assert res.status_code == 200

        # 3. Poll for status
        for _ in range(15): # 15 seconds max to allow for startup and health loop iteration
            res = client.get("/api/plugins")
            assert res.status_code == 200
            plugins = res.json()
            target = next((p for p in plugins if p["id"] == plugin_id), None)
            assert target is not None
            if target["status"] == "running":
                break
            elif target["status"] == "failed":
                pytest.fail(f"Plugin failed to start. Error: {target.get('last_error')}")
            await asyncio.sleep(1)

        assert target["status"] == "running", "Plugin did not reach 'running' state in time."

        # 4. Stop cleanup
        client.post(f"/api/plugins/{plugin_id}/stop")
