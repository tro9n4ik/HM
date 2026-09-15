import pytest
from app.services.plugin_validator import validate_plugin_package, PluginValidationError
import json

def test_manifest_validation(tmp_path):
    plugin_dir = tmp_path / "test_plugin"
    plugin_dir.mkdir()

    # Missing manifest
    with pytest.raises(PluginValidationError, match="manifest.json is missing"):
        validate_plugin_package(plugin_dir)

    # Invalid JSON
    manifest_path = plugin_dir / "manifest.json"
    manifest_path.write_text("{invalid json", encoding="utf-8")
    with pytest.raises(PluginValidationError, match="Invalid JSON"):
        validate_plugin_package(plugin_dir)

    # Valid JSON, missing required fields (name, version)
    manifest_path.write_text('{"description": "missing name"}', encoding="utf-8")
    with pytest.raises(PluginValidationError, match="Manifest schema validation failed"):
        validate_plugin_package(plugin_dir)

    # Hardcoded port forbidden
    manifest_path.write_text('{"name": "valid", "version": "1.0", "port": 8100}', encoding="utf-8")
    with pytest.raises(PluginValidationError, match="cannot hardcode 'port'"):
        validate_plugin_package(plugin_dir)

    # Valid manifest but missing entrypoint
    manifest_path.write_text('{"name": "valid", "version": "1.0", "entrypoint": "main.py"}', encoding="utf-8")
    with pytest.raises(PluginValidationError, match="Entrypoint main.py is missing"):
        validate_plugin_package(plugin_dir)

    # Valid completely
    (plugin_dir / "main.py").write_text("print('hello')", encoding="utf-8")
    manifest = validate_plugin_package(plugin_dir)
    assert manifest.name == "valid"
    assert manifest.version == "1.0"
