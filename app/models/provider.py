from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db import Base

class Clinic(Base):
    __tablename__ = "clinics"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    address = Column(String, nullable=True)
    phone = Column(String, nullable=True)

    providers = relationship("Provider", back_populates="clinic")

class Provider(Base):
    __tablename__ = "providers"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, index=True)
    specialty = Column(String, nullable=True, index=True)
    slug = Column(String, nullable=False, unique=True)
    clinic_id = Column(Integer, ForeignKey("clinics.id"), nullable=True)

    clinic = relationship("Clinic", back_populates="providers")
    hours = relationship("ProviderHours", cascade="all,delete-orphan", back_populates="provider")
    exceptions = relationship("ProviderException", cascade="all,delete-orphan", back_populates="provider")
    appointments = relationship("Appointment", cascade="all,delete-orphan", back_populates="provider")

class ProviderHours(Base):
    """
    Recurring weekly hours. weekday: 0=Mon ... 6=Sun
    start_minute/end_minute: minutes from 00:00 (e.g., 9:00 -> 540, 17:00 -> 1020).
    """
    __tablename__ = "provider_hours"
    id = Column(Integer, primary_key=True)
    provider_id = Column(Integer, ForeignKey("providers.id"), nullable=False)
    weekday = Column(Integer, nullable=False)          # 0..6
    start_minute = Column(Integer, nullable=False)     # 0..1439
    end_minute = Column(Integer, nullable=False)       # > start_minute
    provider = relationship("Provider", back_populates="hours")
    __table_args__ = (UniqueConstraint("provider_id", "weekday", "start_minute", "end_minute", name="uq_hours_span"),)

class ProviderException(Base):
    """
    One-off blocks (vacation/OOO). Times are naive UTC for now.
    """
    __tablename__ = "provider_exceptions"
    id = Column(Integer, primary_key=True)
    provider_id = Column(Integer, ForeignKey("providers.id"), nullable=False)
    start_ts = Column(DateTime, nullable=False)
    end_ts = Column(DateTime, nullable=False)
    reason = Column(String, nullable=True)
    provider = relationship("Provider", back_populates="exceptions")

class Appointment(Base):
    __tablename__ = "appointments"
    id = Column(Integer, primary_key=True)
    patient_email = Column(String, nullable=False)   # simple placeholder instead of FK to users
    provider_id = Column(Integer, ForeignKey("providers.id"), nullable=False)
    start_ts = Column(DateTime, nullable=False)
    end_ts = Column(DateTime, nullable=False)
    status = Column(String, nullable=False, default="booked")  # booked|canceled
    provider = relationship("Provider", back_populates="appointments")
    __table_args__ = (UniqueConstraint("provider_id", "start_ts", name="uq_no_double_book"),)
