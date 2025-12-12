from typing import List, Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    BACKEND_CORS_ORIGINS: List[str] = ["http://theboys-web.eng.unt.edu"]

    # CAPTCHA settings
    RECAPTCHA_SECRET_KEY: Optional[str] = None
    
    # Email settings
    SENDGRID_API_KEY: Optional[str] = None
    SENDGRID_FROM_EMAIL: str = "noreply@easyapt.com"
    
    # SMS settings
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_PHONE_NUMBER: Optional[str] = None
    
    # Test mode settings
    TWILIO_TEST_MODE: str = "false"
    MAILTRAP_MODE: str = "false"



    class Config:
        env_file = ".env"


settings = Settings()
