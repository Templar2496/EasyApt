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
    full_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    phone: Optional[str] = None
    insurance: Optional[str] = None
    insurance_policy_number: Optional[str] = None
    blood_type: Optional[str] = None
    allergies: Optional[str] = None
    medications: Optional[str] = None
    medical_conditions: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None

class PatientProfileUpdate(SQLModel):
    full_name: str
    date_of_birth: date
    phone: str
    insurance: Optional[str] = None
    insurance_policy_number: Optional[str] = None
    blood_type: Optional[str] = None
    allergies: Optional[str] = None
    medications: Optional[str] = None
    medical_conditions: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None

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
    print(f" Received profile data: {profile_in.model_dump()}")
    if profile is None:
        # Create new profile with all fields
        profile = PatientProfile(
            user_id=current_user.id,
            full_name=profile_in.full_name,
            date_of_birth=profile_in.date_of_birth,
            phone=profile_in.phone,
            insurance=profile_in.insurance,
            insurance_policy_number=profile_in.insurance_policy_number,
            blood_type=profile_in.blood_type,
            allergies=profile_in.allergies,
            medications=profile_in.medications,
            medical_conditions=profile_in.medical_conditions,
            emergency_contact_name=profile_in.emergency_contact_name,
            emergency_contact_phone=profile_in.emergency_contact_phone,
        )
        session.add(profile)
    else:
        # Update existing profile with all fields
        profile.full_name = profile_in.full_name
        profile.date_of_birth = profile_in.date_of_birth
        profile.phone = profile_in.phone
        profile.insurance = profile_in.insurance
        profile.insurance_policy_number = profile_in.insurance_policy_number
        profile.blood_type = profile_in.blood_type
        profile.allergies = profile_in.allergies
        profile.medications = profile_in.medications
        profile.medical_conditions = profile_in.medical_conditions
        profile.emergency_contact_name = profile_in.emergency_contact_name
        profile.emergency_contact_phone = profile_in.emergency_contact_phone
    
    session.commit()
    session.refresh(profile)
    return profile
