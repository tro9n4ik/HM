from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.plugin import Plugin, PluginConfig
from app.models.system import SystemSetting
from app.api.deps import get_current_user
from app.services.plugin_manager import plugin_manager
import tempfile
import os
from pydantic import BaseModel
from typing import Dict

router = APIRouter(prefix="/api/plugins", tags=["plugins"])

@router.get("")
def list_plugins(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return db.query(Plugin).all()

@router.post("/install")
def install_plugin(file: UploadFile = File(...), db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    if not file.filename.endswith(".hm"):
        raise HTTPException(status_code=400, detail="Only .hm files are supported")

    plugin_name = file.filename[:-3]

    with tempfile.NamedTemporaryFile(delete=False, suffix=".hm") as tmp:
        tmp.write(file.file.read())
        tmp_path = tmp.name

    try:
        extract_path = plugin_manager.unpack_plugin(tmp_path, plugin_name)

        manifest_path = os.path.join(extract_path, "manifest.json")
        version = "1.0.0"
        if os.path.exists(manifest_path):
            import json
            with open(manifest_path, "r") as f:
                manifest = json.load(f)
                version = manifest.get("version", "1.0.0")
                plugin_name = manifest.get("name", plugin_name)

        plugin = db.query(Plugin).filter(Plugin.name == plugin_name).first()
        if not plugin:
            plugin = Plugin(name=plugin_name, version=version, path=extract_path)
            db.add(plugin)
        else:
            plugin.version = version
            plugin.path = extract_path

        db.commit()
        db.refresh(plugin)

        pip_setting = db.query(SystemSetting).filter_by(key="pip_index_url").first()
        pip_url = pip_setting.value if pip_setting else None

        if not plugin_manager.setup_environment(extract_path, pip_index_url=pip_url):
            plugin.status = "failed"
            plugin.last_error = "Failed to setup environment"
            db.commit()
            raise HTTPException(status_code=500, detail="Failed to setup environment")

        return plugin
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

@router.post("/{plugin_id}/start")
def start_plugin(plugin_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    plugin = db.query(Plugin).filter(Plugin.id == plugin_id).first()
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")

    if not plugin_manager.start_plugin(plugin, db):
        raise HTTPException(status_code=500, detail="Failed to start plugin")

    return {"status": "starting"}

@router.post("/{plugin_id}/stop")
def stop_plugin(plugin_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    plugin = db.query(Plugin).filter(Plugin.id == plugin_id).first()
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")

    plugin_manager.stop_plugin(plugin, db)
    return {"status": "stopped"}

@router.post("/{plugin_id}/restart")
def restart_plugin(plugin_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    plugin = db.query(Plugin).filter(Plugin.id == plugin_id).first()
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")

    plugin_manager.stop_plugin(plugin, db)
    if not plugin_manager.start_plugin(plugin, db):
        raise HTTPException(status_code=500, detail="Failed to restart plugin")

    return {"status": "restarting"}

@router.delete("/{plugin_id}")
def delete_plugin(plugin_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    plugin = db.query(Plugin).filter(Plugin.id == plugin_id).first()
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")

    plugin_manager.stop_plugin(plugin, db)
    db.delete(plugin)
    db.commit()
    return {"status": "deleted"}

@router.get("/{plugin_id}/config")
def get_config(plugin_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    configs = db.query(PluginConfig).filter(PluginConfig.plugin_id == plugin_id).all()
    return {c.key: ("***" if c.is_secret else c.value) for c in configs}

class ConfigUpdate(BaseModel):
    config: Dict[str, str]

@router.put("/{plugin_id}/config")
def update_config(plugin_id: str, req: ConfigUpdate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    plugin = db.query(Plugin).filter(Plugin.id == plugin_id).first()
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")

    for key, value in req.config.items():
        if value == "***":
            continue
        config_entry = db.query(PluginConfig).filter(PluginConfig.plugin_id == plugin_id, PluginConfig.key == key).first()
        if config_entry:
            config_entry.value = value
        else:
            config_entry = PluginConfig(plugin_id=plugin_id, key=key, value=value)
            db.add(config_entry)

    db.commit()
    return {"status": "updated"}

@router.get("/{plugin_id}/logs")
def get_logs(plugin_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    plugin = db.query(Plugin).filter(Plugin.id == plugin_id).first()
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")

    logs = plugin_manager.get_plugin_logs(plugin)
    return {"logs": logs}

@router.get("/{plugin_id}/schema")
def get_plugin_schema(plugin_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    plugin = db.query(Plugin).filter(Plugin.id == plugin_id).first()
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")

    manifest_path = os.path.join(plugin.path, "manifest.json")
    if os.path.exists(manifest_path):
        import json
        try:
            with open(manifest_path, "r") as f:
                manifest = json.load(f)
                return manifest.get("config_schema", {})
        except:
            pass
    return {}
