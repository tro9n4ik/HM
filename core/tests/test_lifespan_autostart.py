import pytest
from app.models.plugin import Plugin
from app.models.system import ActivityLog
from app.main import lifespan
from app.database import Base, engine, SessionLocal
from fastapi import FastAPI
import asyncio
from unittest.mock import patch

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.mark.asyncio
async def test_lifespan_crashed_plugin_does_not_break_startup():
    db = SessionLocal()
    # Insert a plugin with autostart=True and a path that causes an error in start_plugin
    # since path is NOT NULL, we provide a valid string but it points nowhere/is invalid
    bad_plugin = Plugin(
        name="bad_plugin",
        version="1.0.0",
        path="/nonexistent/path/to/nothing",
        autostart=True,
        status="stopped"
    )
    db.add(bad_plugin)
    db.commit()
    db.close()

    app = FastAPI()

    # We mock start_plugin to throw an arbitrary exception
    # since start_plugin itself has its own catch-all internally that masks our Exception catch in lifespan!
    with patch("app.services.plugin_manager.PluginManager.start_plugin") as mock_start:
        mock_start.side_effect = Exception("Simulated unhandled internal exception")
        # Run the lifespan context manager
        async with lifespan(app):
            # The app should start normally without throwing exceptions
            pass

    # Verify the database state after startup attempt
    db = SessionLocal()
    p = db.query(Plugin).filter_by(name="bad_plugin").first()
    assert p is not None
    assert p.status == "failed"
    assert "Autostart crashed:" in p.last_error

    log = db.query(ActivityLog).filter(ActivityLog.message.like("%Autostart failed for plugin 'bad_plugin'%")).first()
    assert log is not None
    db.close()
