import pytest
from app.services.plugin_manager import PluginManager
from app.models.plugin import Plugin
from app.models.system import SystemSetting
from app.database import Base, engine, SessionLocal

@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)

def test_get_free_port(db, tmp_path):
    pm = PluginManager(str(tmp_path))
    port = pm._get_free_port(db, 8100, 8105)
    assert port == 8100

    # Mock a used port
    p = Plugin(name="test", version="1.0", status="running", port=8100, path="/tmp")
    db.add(p)
    db.commit()

    port = pm._get_free_port(db, 8100, 8105)
    assert port == 8101
