from sqlalchemy import Column, Integer, String
from app.db import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    pw_hash = Column(String, nullable=False)
    role = Column(String, nullable=False, default="patient")
