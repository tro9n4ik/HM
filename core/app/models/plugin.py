from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey
from app.database import Base
import uuid
import datetime

class Plugin(Base):
    __tablename__ = "plugins"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, unique=True, index=True, nullable=False)
    version = Column(String, nullable=False)
    status = Column(String, nullable=False, default="stopped") # installing, starting, running, degraded, stopped, failed
    port = Column(Integer, nullable=True)
    path = Column(String, nullable=False)
    autostart = Column(Boolean, default=False)
    last_error = Column(String, nullable=True)
    manifest = Column(String, nullable=True)
    installed_at = Column(DateTime, default=datetime.datetime.utcnow)

class PluginConfig(Base):
    __tablename__ = "plugin_configs"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    plugin_id = Column(String, ForeignKey("plugins.id", ondelete="CASCADE"), nullable=False)
    key = Column(String, nullable=False)
    value = Column(String, nullable=True)
    is_secret = Column(Boolean, default=False)
