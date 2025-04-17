from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime

from database import Base

class SyncLog(Base):
    __tablename__ = "sync_logs"
    
    id = Column(Integer, primary_key=True)
    entity_type = Column(String, nullable=False, unique=True)
    last_sync_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
