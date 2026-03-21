from typing import List, Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    BACKEND_CORS_ORIGINS: List[str] = ["http://theboys-web.eng.unt.edu"]
    
    # CAPTCHA settings
    RECAPTCHA_SECRET_KEY: Optional[str] = None
    
    # === NEW: hCaptcha settings (Emil's) ===
    HCAPTCHA_SECRET_KEY: Optional[str] = None
    HCAPTCHA_SITE_KEY: Optional[str] = None
    
    # Email settings
    SENDGRID_API_KEY: Optional[str] = None
    SENDGRID_FROM_EMAIL: str = "noreply@easyapt.com"
    
    # === NEW: SMTP Email settings (Emil's) ===
    MAILTRAP_HOST: Optional[str] = None
    MAILTRAP_PORT: Optional[str] = None
    MAILTRAP_USERNAME: Optional[str] = None
    MAILTRAP_PASSWORD: Optional[str] = None
    
    # SMS settings
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_PHONE_NUMBER: Optional[str] = None
    
    # Test mode settings
    TWILIO_TEST_MODE: str = "false"
    MAILTRAP_MODE: str = "false"
    
    # === NEW: Appointment & Token settings (Emil's) ===
    LINK_TOKEN_SECRET: Optional[str] = None
    APPOINTMENTS_DB_PATH: str = "appointments.sqlite"
    
    # AI Chatbot
    GROQ_API_KEY: Optional[str] = None

    # --- 2FA settings ---
    TOTP_ISSUER_NAME: str = "EasyApt"
    
    class Config:
        env_file = ".env"

settings = Settings()
