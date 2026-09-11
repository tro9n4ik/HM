from sqlalchemy import Column, String
from app.database import Base

class SystemSetting(Base):
    __tablename__ = "system_settings"
    key = Column(String, primary_key=True)
    value = Column(String, nullable=True)

from sqlalchemy import Integer, DateTime, Text, func
import datetime

class ActivityLog(Base):
    __tablename__ = "activity_logs"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, server_default=func.now())
    source = Column(String(50), nullable=False) # e.g., 'plugin_manager', 'auth'
    message = Column(Text, nullable=False)
