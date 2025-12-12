from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import SQLModel, Session, select

from .database import get_session
from .models import Provider, Appointment, User, PatientProfile, ProviderAppointment
from .auth import get_current_user
from .notification_service import notification_service

router = APIRouter()


# ---------- SCHEMAS ----------

class ProviderCreate(SQLModel):
    name: str
    specialty: Optional[str] = None
    location: Optional[str] = None


class ProviderRead(SQLModel):
    id: int
    name: str
    specialty: Optional[str]
    location: Optional[str]


class AppointmentBook(SQLModel):
    provider_id: int
    start_time: datetime
    end_time: datetime
    reason: Optional[str] = None

class AppointmentRead(SQLModel):
    id: int
    patient_id: int
    provider_id: int
    start_time: datetime
    end_time: datetime
    status: str


class AppointmentReschedule(SQLModel):
    start_time: datetime
    end_time: datetime


# ---------- PROVIDER ENDPOINTS ----------

@router.post("/providers", response_model=ProviderRead)
def create_provider(
    provider_in: ProviderCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Create a provider (for now, allow any logged-in user).
    In a real system, this would be restricted to admin/staff.
    """
    provider = Provider(
        name=provider_in.name,
        specialty=provider_in.specialty,
        location=provider_in.location,
    )
    session.add(provider)
    session.commit()
    session.refresh(provider)
    return provider


@router.get("/providers", response_model=List[ProviderRead])
def list_providers(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    List all providers (basic search for now).
    """
    providers = session.exec(select(Provider)).all()
    return providers

@router.get("/providers/search", response_model=List[Provider])
def search_providers(
    q: str = Query("", description="Search by provider name"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Search providers by partial name match.
    Used by the booking UI when the patient types a name.
    """
    stmt = select(Provider)
    if q:
        stmt = stmt.where(Provider.name.ilike(f"%{q}%"))
    stmt = stmt.order_by(Provider.name)
    return session.exec(stmt).all()

# ---------- APPOINTMENT ENDPOINTS ----------

@router.post("/appointments/book", response_model=Appointment)
async def book_appointment(
    booking: AppointmentBook,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Book an appointment for the current patient with a provider.
    Checks for overlapping appointments for that provider.
    """
    # Make sure provider exists
    provider = session.get(Provider, booking.provider_id)
    if provider is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider not found.",
        )

    if booking.start_time >= booking.end_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_time must be before end_time.",
        )

    # Check for overlapping appointments with this provider
    overlap_stmt = select(Appointment).where(
        Appointment.provider_id == booking.provider_id,
        Appointment.status == "booked",
        Appointment.start_time < booking.end_time,
        Appointment.end_time > booking.start_time,
    )
    existing = session.exec(overlap_stmt).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This time slot is already booked for this provider.",
        )

    appt = Appointment(
        patient_id=current_user.id,
        provider_id=booking.provider_id,
        start_time=booking.start_time,
        end_time=booking.end_time,
        status="booked",
        reason=booking.reason,
    )
    session.add(appt)
    session.commit()
    session.refresh(appt)
    try:
        from .models import PatientProfile
    
        # Get patient profile for name and phone
        profile_stmt = select(PatientProfile).where(PatientProfile.user_id == current_user.id)
        profile = session.exec(profile_stmt).first()
    
        patient_name = profile.full_name if (profile and profile.full_name) else current_user.email.split('@')[0]
        patient_phone = profile.phone if (profile and profile.phone) else ""
    
        # Send notification
        await notification_service.send_booking_confirmation(
            patient_phone=patient_phone,
            patient_email=current_user.email,
            patient_name=patient_name,
            appointment_date=appt.start_time,
            provider_name=provider.name
        )
        print(f"✅ Notification sent to {current_user.email}")
    except Exception as e:
        # Log error but don't fail the booking
        print(f"⚠️ Failed to send notification: {e}")

    return appt

@router.get("/providers/{provider_id}/appointments", response_model=List[Appointment])
def list_provider_appointments(
    provider_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Provider dashboard: list all upcoming appointments for a given provider.
    Used by the booking UI to show which slots are already taken.
    """
    now = datetime.utcnow()
    stmt = (
        select(Appointment)
        .where(Appointment.provider_id == provider_id)
        .where(Appointment.start_time >= now)
        .order_by(Appointment.start_time)
    )
    appts = session.exec(stmt).all()
    return appts



@router.get("/appointments/my", response_model=List[Appointment])
def list_my_appointments(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    List all appointments for the current logged-in patient.
    """
    stmt = select(Appointment).where(Appointment.patient_id == current_user.id)
    appts = session.exec(stmt).all()
    return appts


@router.put("/appointments/{appointment_id}/reschedule", response_model=Appointment)
async def reschedule_appointment(
    appointment_id: int,
    body: AppointmentReschedule,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Reschedule an existing appointment.
    Only the patient who owns it can reschedule.
    """
    appt = session.get(Appointment, appointment_id)
    if appt is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found.",
        )

    if appt.patient_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only reschedule your own appointments.",
        )

    start = body.start_time
    end = body.end_time

    if start.tzinfo is not None:
        start = start.astimezone(timezone.utc).replace(tzinfo=None)
    if end.tzinfo is not None:
        end = end.astimezone(timezone.utc).replace(tzinfo=None)

    if start >= end:
        raise HTTPException(status_code=400, detail="start_time must be before end_time")

    # Check for overlapping appointment with this provider
    overlap_stmt = select(Appointment).where(
        Appointment.provider_id == appt.provider_id,
        Appointment.status == "booked",
        Appointment.id != appt.id,
        Appointment.start_time < end,
        Appointment.end_time > start,
    )
    existing = session.exec(overlap_stmt).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This time slot is already booked for this provider.",
        )

    old_start_time = appt.start_time
    appt.start_time = start
    appt.end_time = end
    session.commit()
    session.refresh(appt)

    # Send reschedule email
    try:
        from .models import PatientProfile
    
        # Get patient profile
        profile_stmt = select(PatientProfile).where(PatientProfile.user_id == current_user.id)
        profile = session.exec(profile_stmt).first()
    
        patient_name = profile.full_name if (profile and profile.full_name) else current_user.email.split('@')[0]
    
        # Get provider
        provider = session.get(Provider, appt.provider_id)
    
        await notification_service.send_reschedule_email(
            patient_email=current_user.email,
            patient_name=patient_name,
            old_date=old_start_time,
            new_date=appt.start_time,
            provider_name=provider.name if provider else "Your provider"
        )
        print(f"✅ Reschedule email sent to {current_user.email}")
    except Exception as e:
        print(f"⚠️ Failed to send reschedule email: {e}")

    return appt


@router.delete("/appointments/{appointment_id}")
async def cancel_appointment(
    appointment_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Cancel an appointment (soft cancel by setting status).
    """
    appt = session.get(Appointment, appointment_id)
    if appt is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found.",
        )

    if appt.patient_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only cancel your own appointments.",
        )

    appt.status = "cancelled"
    session.commit()
    try:
        from .models import PatientProfile
    
        # Get patient profile
        profile_stmt = select(PatientProfile).where(PatientProfile.user_id == current_user.id)
        profile = session.exec(profile_stmt).first()
    
        patient_name = profile.full_name if (profile and profile.full_name) else current_user.email.split('@')[0]
    
        # Get provider
        provider = session.get(Provider, appt.provider_id)
    
        await notification_service.send_cancellation_email(
            patient_email=current_user.email,
            patient_name=patient_name,
            appointment_date=appt.start_time,
            provider_name=provider.name if provider else "Your provider"
        )
        print(f"✅ Cancellation email sent to {current_user.email}")
    except Exception as e:
        print(f"⚠️ Failed to send cancellation email: {e}")

    return {"message": "Appointment cancelled"}

@router.get("/provider-dashboard-list", response_model=list[ProviderAppointment])
def get_provider_dashboard(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Return all upcoming booked appointments for the current provider,
    including patient name and reason.
    """
    if current_user.role != "provider":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Must be logged in as a provider",
        )

    stmt = (
        select(
            Appointment.id,
            Appointment.start_time,
            Appointment.end_time,
            Appointment.status,
            Appointment.reason,          # 👈 include reason
            PatientProfile.full_name,    # 👈 patient_name
        )
        .join(
            PatientProfile,
            PatientProfile.user_id == Appointment.patient_id,
            isouter=True,
        )
        .where(
            Appointment.provider_id == current_user.id,
            Appointment.status == "booked",
        )
        .order_by(Appointment.start_time)
    )

    rows = session.exec(stmt).all()

    results: list[ProviderAppointment] = []
    for row in rows:
        (
            appt_id,
            start_time,
            end_time,
            status_value,
            reason,
            full_name,
        ) = row

        results.append(
            ProviderAppointment(
                id=appt_id,
                start_time=start_time,
                end_time=end_time,
                status=status_value,
                reason=reason,
                patient_name=full_name,
            )
        )

    return results

