import pytest
import os
import shutil
from pathlib import Path

def test_docker_layout_sdk_resolution(tmp_path):
    # Simulate Docker /app directory
    app_dir = tmp_path / "app"
    app_dir.mkdir()

    # Simulate /app/core where plugin_manager.py would live
    core_dir = app_dir / "core"
    services_dir = core_dir / "app" / "services"
    services_dir.mkdir(parents=True)

    # Put a dummy plugin_manager.py there to act as __file__
    manager_file = services_dir / "plugin_manager.py"
    manager_file.touch()

    # Simulate /app/plugins/sdk
    sdk_dir = app_dir / "plugins" / "sdk"
    sdk_dir.mkdir(parents=True)

    sdk_file = sdk_dir / "plugin_sdk.py"
    sdk_file.touch()

    # Emulate the path resolution logic in plugin_manager.py
    # sdk_source = Path(__file__).parent.parent.parent.parent / "plugins" / "sdk" / "plugin_sdk.py"
    resolved_sdk = manager_file.parent.parent.parent.parent / "plugins" / "sdk" / "plugin_sdk.py"

    assert resolved_sdk.resolve() == sdk_file.resolve(), "SDK resolution logic does not point to the expected path in Docker layout"
    assert resolved_sdk.exists(), "SDK file not found - check Dockerfile COPY instructions (plugins directory must be copied)"
