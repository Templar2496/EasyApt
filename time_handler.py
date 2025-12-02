"""
Time Handling Utilities for EasyAPT
Author: Emil K
"""

from datetime import datetime, timedelta, time
from typing import Optional, List, Tuple
import pytz


class TimeHandler:
    
    @staticmethod
    def get_current_utc() -> datetime:
        return datetime.now(pytz.UTC)
    
    @staticmethod
    def convert_to_utc(local_time: datetime, timezone_str: str) -> datetime:
        try:
            local_tz = pytz.timezone(timezone_str)
            if local_time.tzinfo is None:
                local_time = local_tz.localize(local_time)
            else:
                local_time = local_time.astimezone(local_tz)
            return local_time.astimezone(pytz.UTC)
        except pytz.exceptions.UnknownTimeZoneError:
            raise ValueError(f"Invalid timezone: {timezone_str}")
    
    @staticmethod
    def convert_to_local(utc_time: datetime, timezone_str: str) -> datetime:
        try:
            if utc_time.tzinfo is None:
                utc_time = pytz.UTC.localize(utc_time)
            local_tz = pytz.timezone(timezone_str)
            return utc_time.astimezone(local_tz)
        except pytz.exceptions.UnknownTimeZoneError:
            raise ValueError(f"Invalid timezone: {timezone_str}")
    
    @staticmethod
    def validate_appointment_time(appointment_time: datetime, timezone_str: str, min_advance_hours: int = 1) -> Tuple[bool, Optional[str]]:
        now_utc = TimeHandler.get_current_utc()
        if appointment_time.tzinfo is None:
            appointment_time = pytz.UTC.localize(appointment_time)
        if appointment_time <= now_utc:
            return False, "Appointment time cannot be in the past"
        min_time = now_utc + timedelta(hours=min_advance_hours)
        if appointment_time < min_time:
            return False, f"Appointments must be scheduled at least {min_advance_hours} hour(s) in advance"
        max_time = now_utc + timedelta(days=365)
        if appointment_time > max_time:
            return False, "Cannot schedule appointments more than 1 year in advance"
        return True, None
    
    @staticmethod
    def generate_available_slots(start_time: datetime, end_time: datetime, slot_duration_minutes: int = 30, break_times: Optional[List[Tuple[datetime, datetime]]] = None) -> List[datetime]:
        slots = []
        current_time = start_time
        slot_delta = timedelta(minutes=slot_duration_minutes)
        while current_time + slot_delta <= end_time:
            is_available = True
            if break_times:
                for break_start, break_end in break_times:
                    if current_time < break_end and current_time + slot_delta > break_start:
                        is_available = False
                        break
            if is_available:
                slots.append(current_time)
            current_time += slot_delta
        return slots
    
    @staticmethod
    def get_business_hours_utc(business_start: time, business_end: time, local_timezone: str, target_date: datetime) -> Tuple[datetime, datetime]:
        local_tz = pytz.timezone(local_timezone)
        start_naive = datetime.combine(target_date.date(), business_start)
        end_naive = datetime.combine(target_date.date(), business_end)
        start_local = local_tz.localize(start_naive)
        end_local = local_tz.localize(end_naive)
        return start_local.astimezone(pytz.UTC), end_local.astimezone(pytz.UTC)
    
    @staticmethod
    def format_for_display(dt: datetime, timezone_str: str, format_str: str = "%B %d, %Y at %I:%M %p") -> str:
        local_time = TimeHandler.convert_to_local(dt, timezone_str)
        return local_time.strftime(format_str)
    
    @staticmethod
    def get_timezone_offset(timezone_str: str, dt: Optional[datetime] = None) -> str:
        tz = pytz.timezone(timezone_str)
        if dt is None:
            dt = datetime.now()
        localized = tz.localize(dt) if dt.tzinfo is None else dt.astimezone(tz)
        offset = localized.strftime('%z')
        return f"UTC{offset[:3]}:{offset[3:]}"
    
    @staticmethod
    def is_dst_active(timezone_str: str, dt: Optional[datetime] = None) -> bool:
        tz = pytz.timezone(timezone_str)
        if dt is None:
            dt = datetime.now()
        localized = tz.localize(dt) if dt.tzinfo is None else dt.astimezone(tz)
        return bool(localized.dst())
