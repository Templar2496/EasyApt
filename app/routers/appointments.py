from datetime import datetime, timedelta, time
from typing import List, Tuple
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.db import SessionLocal
from app.models import Provider, ProviderHours, ProviderException, Appointment
from app.core.audit import write_audit

router = APIRouter()
SLOT_MINUTES = 30  # granularity

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

def daterange_days(start: datetime, end: datetime):
    cur = start
    while cur.date() <= end.date():
        yield cur
        cur = cur + timedelta(days=1)

def minutes_of_day(dt: datetime) -> int:
    return dt.hour * 60 + dt.minute

def generate_daily_slots(day: datetime, hours: List[ProviderHours]) -> List[Tuple[datetime, datetime]]:
    slots = []
    for h in hours:
        start = datetime.combine(day.date(), time(0,0)) + timedelta(minutes=h.start_minute)
        end = datetime.combine(day.date(), time(0,0)) + timedelta(minutes=h.end_minute)
        cur = start
        while cur + timedelta(minutes=SLOT_MINUTES) <= end:
            slots.append((cur, cur + timedelta(minutes=SLOT_MINUTES)))
            cur += timedelta(minutes=SLOT_MINUTES)
    return slots

def subtract_exceptions(slots: List[Tuple[datetime, datetime]], excs: List[ProviderException]) -> List[Tuple[datetime, datetime]]:
    out = []
    for s in slots:
        blocked = False
        for e in excs:
            if not (s[1] <= e.start_ts or s[0] >= e.end_ts):
                blocked = True; break
        if not blocked:
            out.append(s)
    return out

def subtract_appointments(slots: List[Tuple[datetime, datetime]], appts: List[Appointment]) -> List[Tuple[datetime, datetime]]:
    out = []
    for s in slots:
        taken = False
        for a in appts:
            if a.status == "booked" and not (s[1] <= a.start_ts or s[0] >= a.end_ts):
                taken = True; break
        if not taken:
            out.append(s)
    return out

@router.get("/providers", response_class=HTMLResponse)
def providers_list(request: Request, q: str | None = None, db: Session = Depends(get_db)):
    query = db.query(Provider)
    if q:
        like = f"%{q}%"
        query = query.filter(or_(Provider.name.ilike(like), Provider.specialty.ilike(like)))
    providers = query.order_by(Provider.name.asc()).all()
    return request.app.state.templates.TemplateResponse("providers.html", {"request": request, "providers": providers, "q": q or ""})

@router.get("/providers/{slug}", response_class=HTMLResponse)
def provider_detail(request: Request, slug: str, frm: str | None = None, to: str | None = None, db: Session = Depends(get_db)):
    prov = db.query(Provider).filter_by(slug=slug).first()
    if not prov:
        return RedirectResponse("/appointments/providers", status_code=303)
    start = datetime.fromisoformat(frm) if frm else datetime.now()
    end = datetime.fromisoformat(to) if to else (start + timedelta(days=7))

    day_slots = []
    for day in daterange_days(start, end):
        wd = day.weekday()  # 0..6
        hours = [h for h in prov.hours if h.weekday == wd]
        slots = generate_daily_slots(day, hours)
        excs = db.query(ProviderException).filter(
            ProviderException.provider_id==prov.id,
            ProviderException.start_ts < (day + timedelta(days=1)),
            ProviderException.end_ts > day
        ).all()
        appts = db.query(Appointment).filter(
            Appointment.provider_id==prov.id,
            Appointment.start_ts < (day + timedelta(days=1)),
            Appointment.end_ts > day,
            Appointment.status=="booked"
        ).all()
        slots = subtract_exceptions(slots, excs)
        slots = subtract_appointments(slots, appts)
        if slots:
            day_slots.append((day.date(), slots))

    return request.app.state.templates.TemplateResponse("provider_detail.html", {
        "request": request, "provider": prov, "day_slots": day_slots, "start": start, "end": end
    })

@router.post("/providers/{slug}/book")
def book(
    request: Request,
    slug: str,
    patient_email: str = Form(...),
    slot_start: str = Form(...),
    db: Session = Depends(get_db),
):
    # 1) find provider
    prov = db.query(Provider).filter_by(slug=slug).first()
    if not prov:
        return RedirectResponse("/appointments/providers", status_code=303)

    # 2) parse slot
    try:
        start = datetime.fromisoformat(slot_start)
    except ValueError:
        return RedirectResponse(f"/appointments/providers/{slug}?err=badslot", status_code=303)

    end = start + timedelta(minutes=SLOT_MINUTES)

    # 3) double-book check
    conflict = db.query(Appointment).filter(
        Appointment.provider_id == prov.id,
        Appointment.status == "booked",
        Appointment.start_ts < end,
        Appointment.end_ts > start,
    ).first()

    if conflict is not None:
        return RedirectResponse(f"/appointments/providers/{slug}?err=conflict", status_code=303)

    # 4) create appointment
    try:
        appt = Appointment(
            patient_email=patient_email,
            provider_id=prov.id,
            start_ts=start,
            end_ts=end,
            status="booked",
        )
        db.add(appt)
        db.commit()
    except Exception:
        db.rollback()
        return RedirectResponse(f"/appointments/providers/{slug}?err=server", status_code=303)

    return RedirectResponse(f"/appointments/providers/{slug}?ok=booked", status_code=303)


@router.post("/appointments/{appt_id}/cancel")
def cancel(request: Request, appt_id: int, db: Session = Depends(get_db)):
    appt = db.query(Appointment).get(appt_id)
    if appt and appt.status=="booked":
        appt.status = "canceled"
        write_audit(db, "appt.cancel.success", request, actor=appt.patient_email,
                    resource=f"appointment:{appt.id}")
        db.commit()
    return RedirectResponse("/appointments/providers", status_code=303)
