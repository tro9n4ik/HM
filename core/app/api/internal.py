from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.plugin import PluginConfig, Plugin
from pydantic import BaseModel

router = APIRouter(prefix="/api/internal", tags=["internal"])

def verify_internal(request: Request):
    if request.client.host not in ("127.0.0.1", "::1", "localhost"):
        raise HTTPException(status_code=403, detail="Forbidden")

class RegisterPlugin(BaseModel):
    name: str
    port: int

@router.post("/register", dependencies=[Depends(verify_internal)])
def register_plugin(req: RegisterPlugin, db: Session = Depends(get_db)):
    plugin = db.query(Plugin).filter(Plugin.name == req.name).first()
    if plugin:
        plugin.port = req.port
        plugin.status = "running"
        db.commit()
    return {"status": "ok"}

@router.get("/plugins", dependencies=[Depends(verify_internal)])
def list_internal_plugins(db: Session = Depends(get_db)):
    import json
    plugins = db.query(Plugin).all()
    result = []
    for p in plugins:
        manifest_data = {}
        if p.manifest:
            try:
                manifest_data = json.loads(p.manifest)
            except Exception:
                pass
        result.append({
            "plugin_id": p.id,
            "name": p.name,
            "status": p.status,
            "port": p.port,
            "url": f"http://127.0.0.1:{p.port}" if p.port else None,
            "manifest": manifest_data
        })
    return result

@router.get("/plugins/{plugin_id}/config", dependencies=[Depends(verify_internal)])
def get_internal_config(plugin_id: str, db: Session = Depends(get_db)):
    configs = db.query(PluginConfig).filter(PluginConfig.plugin_id == plugin_id).all()
    # Internal route receives real secrets, no masking
    return {c.key: c.value for c in configs}
