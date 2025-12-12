"""
CAPTCHA Service for EasyAPT
Author: Emil K
"""
import os
import httpx
import logging
from typing import Optional, Dict
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)

class CaptchaService:
    SCORE_THRESHOLD_LOGIN = 0.5
    SCORE_THRESHOLD_REGISTER = 0.6
    VERIFICATION_URL = "https://www.google.com/recaptcha/api/siteverify"
    
    def __init__(self):
        self.secret_key = os.getenv('RECAPTCHA_SECRET_KEY')
        if not self.secret_key:
            logger.warning("reCAPTCHA secret key not configured.")
        self.failed_attempts: Dict[str, list] = defaultdict(list)
        self.rate_limit_window = 300
        self.max_failed_attempts = 10
    
    async def verify_token(self, token: str, action: str = "login", remote_ip: Optional[str] = None) -> Dict[str, any]:
        if not self.secret_key:
            return {"success": False, "score": 0.0, "error": "CAPTCHA not configured"}
        
        data = {"secret": self.secret_key, "response": token}
        if remote_ip:
            data["remoteip"] = remote_ip
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.VERIFICATION_URL, data=data, timeout=10.0)
                result = response.json()
                
                if result.get("success") and result.get("action") != action:
                    result["success"] = False
                    result["error"] = "Action mismatch"
                
                return result
        except Exception as e:
            return {"success": False, "score": 0.0, "error": str(e)}
    
    async def verify_login(self, token: str, remote_ip: Optional[str] = None) -> bool:
        result = await self.verify_token(token, action="login", remote_ip=remote_ip)
        
        if not result.get("success"):
            self._track_failed_attempt(remote_ip)
            return False
        
        score = result.get("score", 0.0)
        if score < self.SCORE_THRESHOLD_LOGIN:
            self._track_failed_attempt(remote_ip)
            return False
        
        if remote_ip:
            self.failed_attempts[remote_ip] = []
        
        return True
    
    def _track_failed_attempt(self, remote_ip: Optional[str]):
        if not remote_ip:
            return
        
        now = datetime.now()
        self.failed_attempts[remote_ip].append(now)
        
        cutoff = now - timedelta(seconds=self.rate_limit_window)
        self.failed_attempts[remote_ip] = [t for t in self.failed_attempts[remote_ip] if t > cutoff]
    
    def is_rate_limited(self, remote_ip: str) -> bool:
        if remote_ip not in self.failed_attempts:
            return False
        
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.rate_limit_window)
        recent = [t for t in self.failed_attempts[remote_ip] if t > cutoff]
        
        return len(recent) >= self.max_failed_attempts
    
    def get_failed_attempt_count(self, remote_ip: str) -> int:
        if remote_ip not in self.failed_attempts:
            return 0
        
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.rate_limit_window)
        return len([t for t in self.failed_attempts[remote_ip] if t > cutoff])

captcha_service = CaptchaService()
