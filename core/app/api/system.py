from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.system import SystemSetting
from app.models.plugin import PluginConfig, Plugin
from app.api.deps import get_current_user
from pydantic import BaseModel
from typing import Dict
import tempfile
import json
import os

router = APIRouter(prefix="/api/system", tags=["system"])

@router.get("/setup-status")
def get_setup_status(db: Session = Depends(get_db)):
    return {"setup_required": db.query(User).first() is None}

class SettingsUpdate(BaseModel):
    settings: Dict[str, str]

@router.get("/settings")
def get_settings(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    settings = db.query(SystemSetting).all()
    return {s.key: s.value for s in settings}

@router.put("/settings")
def update_settings(req: SettingsUpdate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    for key, value in req.settings.items():
        setting = db.query(SystemSetting).filter_by(key=key).first()
        if setting:
            setting.value = value
        else:
            setting = SystemSetting(key=key, value=value)
            db.add(setting)
    db.commit()
    return {"status": "updated"}

@router.post("/backup")
def backup_system(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    configs = db.query(PluginConfig).all()
    # Mask secrets
    export_data = []
    for c in configs:
        if c.is_secret:
            continue # Don't export secrets in plain text backup for security
        export_data.append({
            "plugin_id": c.plugin_id,
            "key": c.key,
            "value": c.value,
            "is_secret": c.is_secret
        })

    system_settings = db.query(SystemSetting).all()
    sys_export = [{"key": s.key, "value": s.value} for s in system_settings]

    backup_payload = {
        "configs": export_data,
        "settings": sys_export
    }

    tmp_path = os.path.join(tempfile.gettempdir(), "hm_backup.json")
    with open(tmp_path, "w") as f:
        json.dump(backup_payload, f)

    return FileResponse(tmp_path, filename="hm_backup.json", media_type="application/json")

@router.post("/restore")
def restore_system(file: UploadFile = File(...), db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    if not file.filename.endswith(".json"):
        raise HTTPException(status_code=400, detail="Only JSON backups are supported")

    try:
        content = file.file.read()
        data = json.loads(content)

        configs = data.get("configs", [])
        for c in configs:
            existing = db.query(PluginConfig).filter_by(plugin_id=c["plugin_id"], key=c["key"]).first()
            if existing:
                existing.value = c["value"]
            else:
                new_c = PluginConfig(plugin_id=c["plugin_id"], key=c["key"], value=c["value"], is_secret=c.get("is_secret", False))
                db.add(new_c)

        settings = data.get("settings", [])
        for s in settings:
            existing_sys = db.query(SystemSetting).filter_by(key=s["key"]).first()
            if existing_sys:
                existing_sys.value = s["value"]
            else:
                new_s = SystemSetting(key=s["key"], value=s["value"])
                db.add(new_s)

        db.commit()
        return {"status": "restored"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to restore: {str(e)}")

@router.get("/info")
def get_system_info(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    import platform
    return {
        "os": platform.system(),
        "release": platform.release(),
        "version": "1.0.0",
        "plugins_count": db.query(Plugin).count()
    }
