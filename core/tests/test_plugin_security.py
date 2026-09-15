import pytest
import zipfile
import os
from pathlib import Path
from app.services.plugin_manager import PluginManager
from app.services.plugin_validator import PluginValidationError

def test_unpack_plugin_blocks_zip_slip(tmp_path):
    manager = PluginManager(str(tmp_path / "data"))
    malicious_zip = tmp_path / "malicious.zip"

    # Create a malicious zip with absolute path
    with zipfile.ZipFile(malicious_zip, 'w') as zf:
        # absolute path
        zf.writestr("/etc/passwd", "fake")
        # path traversal
        zf.writestr("../../../../../tmp/hacked", "fake")

    with pytest.raises(PluginValidationError, match="Unsafe archive path|Zip-slip attempt detected"):
        manager.unpack_plugin(str(malicious_zip), "test_plugin")

def test_unpack_plugin_blocks_zip_bomb(tmp_path):
    manager = PluginManager(str(tmp_path / "data"))
    bomb_zip = tmp_path / "bomb.zip"

    with zipfile.ZipFile(bomb_zip, 'w') as zf:
        # 2001 files (exceeds MAX_FILES)
        for i in range(2001):
            zf.writestr(f"file_{i}.txt", "data")

    with pytest.raises(PluginValidationError, match="Plugin archive contains too many files"):
        manager.unpack_plugin(str(bomb_zip), "test_plugin")

def test_unpack_plugin_blocks_large_size(tmp_path, monkeypatch):
    manager = PluginManager(str(tmp_path / "data"))

    # We can mock the ZipFile infolist to pretend it's huge
    class MockZipFile:
        def __init__(self, *args, **kwargs):
            pass
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def extractall(self, *args, **kwargs): pass
        def infolist(self):
            class FakeInfo:
                def __init__(self):
                    self.file_size = 600 * 1024 * 1024 # 600 MB
                    self.filename = "huge_file.txt"
            return [FakeInfo()]

    monkeypatch.setattr("zipfile.ZipFile", MockZipFile)

    with pytest.raises(PluginValidationError, match="Plugin archive uncompressed size is too large"):
        manager.unpack_plugin("fake.zip", "test_plugin")
