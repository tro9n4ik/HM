from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.api import auth, system, proxy, plugins, internal
from contextlib import asynccontextmanager
from app.database import SessionLocal
import asyncio
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.services.plugin_manager import plugin_manager
    from app.models.plugin import Plugin

    db = SessionLocal()
    try:
        plugins = db.query(Plugin).filter(Plugin.autostart == True).all()
        for p in plugins:
            plugin_manager.start_plugin(p, db)
    finally:
        db.close()

    health_task = asyncio.create_task(plugin_manager.healthcheck_loop(SessionLocal))

    yield

    health_task.cancel()

    db = SessionLocal()
    try:
        plugins = db.query(Plugin).filter(Plugin.status.in_(["starting", "running", "degraded"])).all()
        for p in plugins:
            plugin_manager.stop_plugin(p, db)
    finally:
        db.close()

app = FastAPI(title="Home.Media Core API", lifespan=lifespan)

app.include_router(auth.router)
app.include_router(system.router)
app.include_router(proxy.router)
app.include_router(plugins.router)
app.include_router(internal.router)

@app.get("/health")
def healthcheck():
    return {"status": "ok"}

# Serve React App
static_dir = os.path.join(os.path.dirname(__file__), "web", "static", "admin")
assets_dir = os.path.join(static_dir, "assets")

# Only mount the static assets directory if it exists, to avoid crashing tests
# when the frontend hasn't been built yet.
if os.path.exists(assets_dir):
    app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

# Catch-all route to serve React's index.html for client-side routing
@app.get("/{full_path:path}")
async def serve_react_app(full_path: str):
    if full_path.startswith("api/") or full_path.startswith("plugins/"):
        # Avoid masking API and Proxy 404s
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Not found")

    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"error": "Frontend not built"}
