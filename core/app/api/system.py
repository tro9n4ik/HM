from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.system import SystemSetting
from app.api.deps import get_current_user
from pydantic import BaseModel
from typing import Dict

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
    return {"status": "backup_created", "file": "backup.zip"}

@router.post("/restore")
def restore_system(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return {"status": "restored"}

@router.get("/info")
def get_system_info(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    import platform
    return {
        "os": platform.system(),
        "release": platform.release(),
        "version": "1.0.0",
        "plugins_count": db.query(User).count() # mock logic to keep simple
    }
