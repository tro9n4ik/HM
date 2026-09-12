import pytest
from app.services.plugin_manager import PluginManager
from app.models.plugin import Plugin
from app.models.system import SystemSetting
from app.database import Base, engine, SessionLocal
from unittest import mock

@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)

@mock.patch("socket.socket")
def test_get_free_port(mock_socket, db, tmp_path):
    mock_socket.return_value.__enter__.return_value.connect_ex.return_value = 1 # Not in use

    pm = PluginManager(str(tmp_path))
    port = pm._get_free_port(db, 8100, 8105)
    assert port == 8100

    # Mock a used port
    p = Plugin(name="test_port", version="1.0", status="running", port=8100, path="/tmp")
    db.add(p)
    db.commit()

    port = pm._get_free_port(db, 8100, 8105)
    assert port == 8101

def test_venv_python_resolution(tmp_path):
    import os
    pm = PluginManager(str(tmp_path))

    plugin_path_str = str(tmp_path / "test_venv_res")
    os.makedirs(plugin_path_str, exist_ok=True)
    with open(os.path.join(plugin_path_str, "requirements.txt"), "w") as f:
        f.write("fastapi\n")

    pm.setup_environment(plugin_path_str)

    # We want to verify that executing python from the venv resolves to the venv site-packages
    # and not the global environment. We will just print the path of a built-in module loaded from within the venv
    import subprocess
    from pathlib import Path

    venv_python = Path(plugin_path_str) / "venv" / "bin" / "python"

    res = subprocess.run([str(venv_python), "-c", "import fastapi; print(fastapi.__file__)"], capture_output=True, text=True)
    assert res.returncode == 0
    assert "venv" in res.stdout, f"fastapi was not loaded from the venv! Output: {res.stdout}"
