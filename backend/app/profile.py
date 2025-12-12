from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends
from sqlmodel import SQLModel, Session, select

from .database import get_session
from .models import PatientProfile, User
from .auth import get_current_user

router = APIRouter()


class PatientProfileRead(SQLModel):
    id: int
    user_id: int
    full_name: str
    date_of_birth: date
    phone: str
    insurance: Optional[str]


class PatientProfileUpdate(SQLModel):
    full_name: str
    date_of_birth: date
    phone: str
    insurance: Optional[str] = None


@router.get("/me", response_model=Optional[PatientProfileRead])
def get_my_profile(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Get the current logged-in patient's profile.
    Returns null if no profile exists yet.
    """
    statement = select(PatientProfile).where(PatientProfile.user_id == current_user.id)
    return session.exec(statement).first()


@router.put("/me", response_model=PatientProfileRead)
def upsert_my_profile(
    profile_in: PatientProfileUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Create or update the current patient's profile.
    """
    statement = select(PatientProfile).where(PatientProfile.user_id == current_user.id)
    profile = session.exec(statement).first()

    if profile is None:
        profile = PatientProfile(
            user_id=current_user.id,
            full_name=profile_in.full_name,
            date_of_birth=profile_in.date_of_birth,
            phone=profile_in.phone,
            insurance=profile_in.insurance,
        )
        session.add(profile)
    else:
        profile.full_name = profile_in.full_name
        profile.date_of_birth = profile_in.date_of_birth
        profile.phone = profile_in.phone
        profile.insurance = profile_in.insurance

    session.commit()
    session.refresh(profile)
    return profile
