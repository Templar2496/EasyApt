from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from ..core.settings import settings
from ..db.session import SessionLocal
from ..models.base import Base
from ..models.user import User
from ..security.passwords import hash_password, meets_policy, verify_password
from ..security.tokens import create_access

router = APIRouter(tags=["auth"])

# Day-1 simple create tables
engine = create_engine(settings.DB_URL)
Base.metadata.create_all(bind=engine)


class RegisterIn(BaseModel):
    email: EmailStr
    password: str


class LoginIn(BaseModel):
    email: EmailStr
    password: str
    totp: str | None = None


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/register", status_code=201)
def register(data: RegisterIn, db: Session = Depends(get_db)):
    if not meets_policy(data.password):
        raise HTTPException(400, "Password does not meet complexity policy")
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(409, "Email already registered")
    u = User(email=data.email, pw_hash=hash_password(data.password))
    db.add(u)
    db.commit()
    return {"ok": True}


@router.post("/login", response_model=TokenOut)
def login(data: LoginIn, db: Session = Depends(get_db)):
    u = db.query(User).filter(User.email == data.email).first()
    if not u or u.is_locked:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    if not verify_password(data.password, u.pw_hash):
        u.failed_logins += 1
        if u.failed_logins >= settings.LOCKOUT_THRESHOLD:
            u.is_locked = True
        db.commit()
        raise HTTPException(401, "Invalid credentials")
    # optional TOTP check if enrolled (will add enroll flow later)
    if u.totp_secret:
        import pyotp

        if not data.totp or not pyotp.TOTP(u.totp_secret).verify(
            data.totp, valid_window=1
        ):
            raise HTTPException(401, "TOTP required/invalid")
    u.failed_logins = 0
    db.commit()
    return TokenOut(access_token=create_access(str(u.id), roles=["patient"]))
