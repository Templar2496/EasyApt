from datetime import datetime, date
from typing import Optional

from sqlmodel import SQLModel, Field, Relationship


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    password_hash: str
    role: str = Field(default="patient")  # patient, provider, staff, admin
    created_at: datetime = Field(default_factory=datetime.utcnow)

    failed_login_attempts: int = Field(default=0)
    lockout_until: Optional[datetime] = Field(default=None)

    last_active: Optional[datetime] = Field(default=None)

class PatientProfile(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True, foreign_key="user.id")
    full_name: str
    date_of_birth: date
    phone: str
    insurance: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Provider(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    specialty: Optional[str] = None
    location: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Appointment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    patient_id: int = Field(foreign_key="user.id", index=True)
    provider_id: int = Field(foreign_key="provider.id", index=True)
    start_time: datetime
    end_time: datetime
    status: str = Field(default="booked")  # booked, cancelled, completed, etc.
    reason: Optional[str] = Field(default=None, max_length=255)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ProviderAppointment(SQLModel):
    id: int
    start_time: datetime
    end_time: datetime
    status: str
    reason: Optional[str] = None
    patient_name: Optional[str] = None
