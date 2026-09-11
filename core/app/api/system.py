from sqlalchemy import text
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

import psutil

def _human_bytes(size: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"

@router.get("/stats")
def get_stats(current_user=Depends(get_current_user)):
    cpu_percent = psutil.cpu_percent(interval=0.3)
    vm = psutil.virtual_memory()
    disk = psutil.disk_usage(os.environ.get("DATA_DIR", "/"))

    try:
        load_avg = f"{os.getloadavg()[0]:.2f}"
    except AttributeError:
        load_avg = "--"

    return {
        "cpu": {"percent": cpu_percent, "load": load_avg},
        "memory": {
            "percent": vm.percent,
            "used": _human_bytes(vm.used),
            "total": _human_bytes(vm.total),
        },
        "storage": {
            "percent": disk.percent,
            "used": _human_bytes(disk.used),
            "total": _human_bytes(disk.total),
        },
    }

@router.get("/health")
def get_health(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    plugins = db.query(Plugin).all()
    checks = []

    # Internal DB check as a baseline
    try:
        db.execute(text("SELECT 1"))
        checks.append({"name": "Database", "status": "ok", "message": "connected"})
    except Exception as e:
        checks.append({"name": "Database", "status": "error", "message": str(e)})

    for p in plugins:
        if p.status == "running":
            checks.append({"name": f"Plugin: {p.name}", "status": "ok", "message": "running"})
        elif p.status == "degraded":
            checks.append({"name": f"Plugin: {p.name}", "status": "error", "message": "degraded"})
        elif p.status == "failed":
            checks.append({"name": f"Plugin: {p.name}", "status": "error", "message": p.last_error or "failed"})
        # We don't include stopped/starting in health errors for now

    return checks

from app.models.system import ActivityLog

@router.get("/activity")
def get_activity(limit: int = 10, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    events = db.query(ActivityLog).order_by(ActivityLog.timestamp.desc()).limit(limit).all()
    # Format according to frontend expectations
    return [{
        "time": e.timestamp.strftime("%H:%M:%S"),
        "message": e.message,
        "source": e.source
    } for e in events]
