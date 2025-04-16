from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from database import Base


class Account(Base):
    __tablename__ = "accounts"
    
    id = Column(Integer, primary_key=True)
    qbo_id = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    classification = Column(String)
    currency_ref = Column(String)
    account_type = Column(String)
    active = Column(Boolean, default=True)
    current_balance = Column(Float)
    parent_id = Column(String, ForeignKey('accounts.qbo_id'), nullable=True)
    last_synced_at = Column(DateTime, default=datetime.utcnow)
    
    children = relationship("Account", backref="parent", remote_side=[qbo_id])
