from sqlalchemy import Column, Integer, String, DateTime, JSON
from datetime import datetime
from app.db import Base

class AuditLog(Base):
    __tablename__ = "audit_log"
    id = Column(Integer, primary_key=True)
    ts = Column(DateTime, default=datetime.utcnow, nullable=False)
    actor = Column(String, nullable=True)          # e.g., email (or user id later)
    ip = Column(String, nullable=True)
    ua = Column(String, nullable=True)             # user-agent
    action = Column(String, nullable=False)        # e.g., auth.login, appt.book
    resource = Column(String, nullable=True)       # e.g., appointment:123
    details = Column(JSON, nullable=True)          # small structured context
