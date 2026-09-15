import json
from pathlib import Path
from pydantic import BaseModel, Field, ValidationError
from typing import Dict, Any, Optional

class PluginValidationError(Exception):
    pass

class PluginManifest(BaseModel):
    name: str = Field(pattern=r"^[a-zA-Z0-9_-]+$")
    version: str
    description: str = ""
    web_ui: bool = False
    config_schema: Dict[str, Any] = Field(default_factory=dict)
    bot_menu: Optional[Dict[str, Any]] = None
    sdk_version: Optional[str] = None
    entrypoint: str = "main.py"

def load_and_validate_manifest(manifest_path: Path) -> PluginManifest:
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise PluginValidationError(f"Invalid JSON in manifest.json: {e}")
    except Exception as e:
        raise PluginValidationError(f"Failed to read manifest.json: {e}")

    # Validate forbidden hardcoded ports
    if "port" in data:
        raise PluginValidationError("Manifest cannot hardcode 'port'")

    try:
        return PluginManifest(**data)
    except ValidationError as e:
        raise PluginValidationError(f"Manifest schema validation failed: {e}")

def validate_plugin_package(path: Path) -> PluginManifest:
    manifest_path = path / "manifest.json"

    if not manifest_path.exists():
        raise PluginValidationError("manifest.json is missing")

    manifest = load_and_validate_manifest(manifest_path)

    entrypoint_path = path / manifest.entrypoint
    if not entrypoint_path.exists():
        raise PluginValidationError(f"Entrypoint {manifest.entrypoint} is missing")

    # Additional validations can go here (e.g. requirements.txt)

    return manifest
