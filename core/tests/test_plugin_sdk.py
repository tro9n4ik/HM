import pytest
import os
import json
from unittest.mock import AsyncMock, patch

# Ensure test can load the sdk
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../plugins/sdk')))
from plugin_sdk import PluginApp, Config

@pytest.fixture
def mock_env():
    os.environ["CORE_INTERNAL_URL"] = "http://test-core:8000"
    os.environ["PLUGIN_PORT"] = "9999"
    os.environ["PLUGIN_ID"] = "test-plugin-123"
    yield
    del os.environ["CORE_INTERNAL_URL"]
    del os.environ["PLUGIN_PORT"]
    del os.environ["PLUGIN_ID"]

@pytest.mark.asyncio
async def test_plugin_app_load_config(mock_env):
    app = PluginApp("my_plugin")

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"API_KEY": "secret123", "DEBUG": "true"}

        await app._load_config()

        assert app.config.get("API_KEY") == "secret123"
        assert app.config.get("DEBUG") == "true"
        mock_get.assert_called_with("http://test-core:8000/api/internal/plugins/test-plugin-123/config", timeout=5.0)

@pytest.mark.asyncio
async def test_plugin_app_resolve_plugin(mock_env):
    app = PluginApp("my_plugin")

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = [
            {"name": "other_plugin", "url": "http://127.0.0.1:8005"}
        ]

        target = await app.resolve_plugin("other_plugin")

        assert target is not None
        assert target["url"] == "http://127.0.0.1:8005"
        mock_get.assert_called_with("http://test-core:8000/api/internal/plugins", timeout=5.0)

def test_plugin_app_healthcheck():
    from fastapi.testclient import TestClient
    app = PluginApp("test_health")
    client = TestClient(app)

    # Default is ok
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}

    # Degraded
    app.ready = False
    app.ready_detail = "Missing config"
    resp2 = client.get("/health")
    assert resp2.status_code == 503
    assert resp2.json() == {"status": "degraded", "detail": "Missing config"}
