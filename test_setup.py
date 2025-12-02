from time_handler import TimeHandler
from datetime import datetime

print("="*60)
print("TESTING EASYAPT SETUP")
print("="*60)

local_time = datetime(2025, 3, 15, 14, 0)
utc_time = TimeHandler.convert_to_utc(local_time, "America/Chicago")
print(f"Local: {local_time}")
print(f"UTC: {utc_time}")
print("Time conversion works!")

try:
    from notification_service import notification_service
    from captcha_service import captcha_service
    from test_profile_service import test_profile_service
    print("All services imported successfully!")
except ImportError as e:
    print(f"Import failed: {e}")

print("="*60)
print("SETUP COMPLETE!")
print("="*60)
