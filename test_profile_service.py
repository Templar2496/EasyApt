"""
Test Profile Service for EasyAPT
Author: Emil K
"""

from datetime import datetime, timedelta
from typing import Optional, Dict
import secrets
import string
import logging

logger = logging.getLogger(__name__)


class TestProfileService:
    TEST_PROFILE_EXPIRY_DAYS = 7
    TEST_USERNAME_PREFIX = "test_"
    TEST_EMAIL_DOMAIN = "@test.easyapt.local"
    
    def __init__(self, database_connection=None):
        self.db = database_connection
    
    def generate_test_credentials(self) -> Dict[str, str]:
        random_suffix = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(8))
        username = f"{self.TEST_USERNAME_PREFIX}{random_suffix}"
        email = f"{username}{self.TEST_EMAIL_DOMAIN}"
        password = self._generate_secure_password()
        return {"username": username, "email": email, "password": password}
    
    def _generate_secure_password(self, length: int = 12) -> str:
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        while True:
            password = ''.join(secrets.choice(alphabet) for _ in range(length))
            has_lower = any(c.islower() for c in password)
            has_upper = any(c.isupper() for c in password)
            has_digit = any(c.isdigit() for c in password)
            has_symbol = any(c in "!@#$%^&*" for c in password)
            if has_lower and has_upper and has_digit and has_symbol:
                return password
    
    async def create_test_profile(self, custom_username: Optional[str] = None) -> Dict[str, any]:
        if custom_username:
            random_suffix = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(4))
            credentials = {
                "username": f"{self.TEST_USERNAME_PREFIX}{custom_username}_{random_suffix}",
                "email": f"{self.TEST_USERNAME_PREFIX}{custom_username}_{random_suffix}{self.TEST_EMAIL_DOMAIN}",
                "password": self._generate_secure_password()
            }
        else:
            credentials = self.generate_test_credentials()
        
        expiry_date = datetime.now() + timedelta(days=self.TEST_PROFILE_EXPIRY_DAYS)
        
        return {
            "success": True,
            "user_id": 9999,
            "username": credentials["username"],
            "email": credentials["email"],
            "password": credentials["password"],
            "expires_at": expiry_date.isoformat(),
            "message": "Test profile created successfully."
        }


test_profile_service = TestProfileService()
