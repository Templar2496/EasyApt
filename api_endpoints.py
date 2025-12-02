from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime, time
from typing import Optional
from time_handler import TimeHandler
from captcha_service import captcha_service
from test_profile_service import test_profile_service

router = APIRouter()

class TimeConversionRequest(BaseModel):
    datetime_str: str
    from_timezone: str
    to_timezone: str

class AppointmentValidationRequest(BaseModel):
    date: str
    time: str
    timezone: str
    min_advance_hours: int = 1

@router.post("/time/convert")
async def convert_time(request: TimeConversionRequest):
    try:
        dt = datetime.fromisoformat(request.datetime_str)
        utc_time = TimeHandler.convert_to_utc(dt, request.from_timezone)
        converted = TimeHandler.convert_to_local(utc_time, request.to_timezone)
        return {"original": request.datetime_str, "converted": converted.isoformat()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/time/validate-appointment")
async def validate_appointment(request: AppointmentValidationRequest):
    try:
        dt = datetime.fromisoformat(f"{request.date}T{request.time}")
        utc_time = TimeHandler.convert_to_utc(dt, request.timezone)
        is_valid, error = TimeHandler.validate_appointment_time(utc_time, request.timezone, request.min_advance_hours)
        return {"valid": is_valid, "error": error}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/health")
async def health_check():
    return {"status": "healthy"}
