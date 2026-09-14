import pytest
from app.models.plugin import Plugin
from app.services.plugin_manager import plugin_manager
from app.database import Base, engine, SessionLocal
from unittest.mock import patch

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_start_plugin_reassigns_port_if_in_use():
    db = SessionLocal()
    plugin = Plugin(
        name="test_port_plugin",
        version="1.0.0",
        path="/tmp",
        autostart=True,
        status="stopped",
        port=8105
    )
    db.add(plugin)
    db.commit()

    # We want to mock socket.socket.connect_ex such that:
    # 1. When it checks the existing port 8105, it returns 0 (occupied)
    # 2. When it checks the new port (e.g., 8100) during _get_free_port, it returns 1 (free)

    with patch('socket.socket') as mock_socket:
        mock_instance = mock_socket.return_value.__enter__.return_value

        def side_effect(address):
            if address[1] == 8105:
                return 0 # simulate port is IN USE
            return 1 # simulate port is FREE

        mock_instance.connect_ex.side_effect = side_effect

        # We mock Popen so it doesn't actually try to start a plugin process
        with patch('subprocess.Popen'):
            with patch('builtins.open'):
                result = plugin_manager.start_plugin(plugin, db)

    db.refresh(plugin)
    assert result is True
    assert plugin.port != 8105 # Port should have been reassigned
    assert plugin.port >= 8100 and plugin.port <= 8200
    assert plugin.status == "starting"

    db.close()
