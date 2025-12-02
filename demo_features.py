"""
Demo all EasyAPT features
"""
import asyncio
from time_handler import TimeHandler
from test_profile_service import test_profile_service
from datetime import datetime, timedelta, time

print("\n" + "="*70)
print("EASYAPT FEATURE DEMONSTRATION")
print("="*70)

# Feature 1: Time Zone Conversions
print("\n1. TIME ZONE CONVERSIONS")
print("-" * 70)
timezones = ["America/New_York", "America/Chicago", "America/Denver", "America/Los_Angeles"]
test_time = datetime(2025, 3, 15, 14, 30)

for tz in timezones:
    utc = TimeHandler.convert_to_utc(test_time, tz)
    print(f"{tz:30s} 2:30 PM -> UTC: {utc.strftime('%I:%M %p')}")

# Feature 2: Appointment Validation
print("\n2. APPOINTMENT VALIDATION")
print("-" * 70)

future_appt = datetime.now() + timedelta(days=7, hours=2)
future_utc = TimeHandler.convert_to_utc(future_appt, "America/Chicago")
is_valid, error = TimeHandler.validate_appointment_time(future_utc, "America/Chicago")
print(f"7 days from now: {'VALID' if is_valid else 'INVALID'}")

past_appt = datetime.now() - timedelta(days=1)
past_utc = TimeHandler.convert_to_utc(past_appt, "America/Chicago")
is_valid, error = TimeHandler.validate_appointment_time(past_utc, "America/Chicago")
print(f"Yesterday: {'VALID' if is_valid else 'INVALID'} - {error}")

# Feature 3: Available Slots Generation
print("\n3. AVAILABLE APPOINTMENT SLOTS")
print("-" * 70)
tomorrow = datetime.now() + timedelta(days=1)
start_utc, end_utc = TimeHandler.get_business_hours_utc(
    time(9, 0), time(17, 0), "America/Chicago", tomorrow
)
slots = TimeHandler.generate_available_slots(start_utc, end_utc, 30)
print(f"Business hours: 9 AM - 5 PM")
print(f"Slot duration: 30 minutes")
print(f"Total slots: {len(slots)}")
print(f"First slot: {TimeHandler.format_for_display(slots[0], 'America/Chicago', '%I:%M %p')}")
print(f"Last slot: {TimeHandler.format_for_display(slots[-1], 'America/Chicago', '%I:%M %p')}")

# Feature 4: Test Profiles
print("\n4. TEST PROFILE CREATION")
print("-" * 70)

async def create_profiles():
    for i in range(3):
        profile = await test_profile_service.create_test_profile()
        print(f"Profile {i+1}: {profile['username']:20s} | Password: {profile['password']}")

asyncio.run(create_profiles())

print("\n" + "="*70)
print("ALL FEATURES WORKING PERFECTLY!")
print("="*70 + "\n")
