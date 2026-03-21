from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel
import re
import json
import io
import base64
import secrets

import pyotp
import qrcode

from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlmodel import SQLModel, Session, select
from jose import JWTError, jwt
from passlib.context import CryptContext
from .notification_service import notification_service
import logging
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHash

from .config import settings
from .database import get_session
from .models import User
from .captcha_service import captcha_service

PASSWORD_POLICY = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{12,}$")

def meets_password_policy(password: str) -> bool:
    return bool(PASSWORD_POLICY.match(password))


router = APIRouter()
logger = logging.getLogger(__name__)

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
INACTIVITY_TIMEOUT_SECONDS = 300

ph = PasswordHasher()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# Temporary token used only between password step and 2FA step
TWO_FACTOR_TEMP_EXPIRE_MINUTES = 10


# --- Schemas ---

class UserCreate(SQLModel):
    email: str
    password: str
    role: Optional[str] = "patient"


class UserRead(SQLModel):
    id: int
    email: str
    role: str
    created_at: datetime


class Token(SQLModel):
    access_token: str
    token_type: str


class TokenData(SQLModel):
    user_id: Optional[int] = None


class LoginRequest(BaseModel):
    email: str
    password: str
    captcha_token: str


class LoginStartResponse(SQLModel):
    requires_2fa: bool
    access_token: Optional[str] = None
    token_type: Optional[str] = None
    temp_token: Optional[str] = None


class Login2FARequest(SQLModel):
    temp_token: str
    code: str


class TwoFactorStatusResponse(SQLModel):
    enabled: bool


class TwoFactorSetupStartResponse(SQLModel):
    secret: str
    otpauth_url: str
    qr_code_base64: str


class TwoFactorSetupVerifyRequest(SQLModel):
    code: str


class TwoFactorDisableRequest(SQLModel):
    password: str
    code: str


class BackupCodesResponse(SQLModel):
    backup_codes: list[str]


# --- Helper functions ---

def get_password_hash(password: str) -> str:
    return ph.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return ph.verify(hashed_password, plain_password)
    except (VerifyMismatchError, VerificationError, InvalidHash):
        try:
            pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
            return pwd_context.verify(plain_password, hashed_password)
        except Exception:
            return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_temp_2fa_token(user: User) -> str:
    expire = datetime.utcnow() + timedelta(minutes=TWO_FACTOR_TEMP_EXPIRE_MINUTES)
    payload = {
        "sub": str(user.id),
        "type": "2fa_temp",
        "exp": expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_temp_2fa_token(temp_token: str) -> int:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired 2FA session.",
    )
    try:
        payload = jwt.decode(temp_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "2fa_temp":
            raise credentials_exception
        sub = payload.get("sub")
        if sub is None:
            raise credentials_exception
        return int(sub)
    except (JWTError, ValueError):
        raise credentials_exception


def get_user_by_email(session: Session, email: str) -> Optional[User]:
    statement = select(User).where(User.email == email)
    result = session.exec(statement)
    return result.first()


def authenticate_user(session: Session, email: str, password: str) -> Optional[User]:
    user = get_user_by_email(session, email)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def build_totp(secret: str) -> pyotp.TOTP:
    return pyotp.TOTP(secret)


def make_qr_code_base64(data: str) -> str:
    qr = qrcode.QRCode(box_size=8, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return encoded


def generate_backup_codes(count: int = 8) -> list[str]:
    codes = []
    for _ in range(count):
        code = secrets.token_hex(4).upper()
        codes.append(code)
    return codes


def load_backup_codes(user: User) -> list[str]:
    if not user.two_factor_backup_codes:
        return []
    try:
        return json.loads(user.two_factor_backup_codes)
    except Exception:
        return []


def save_backup_codes(user: User, codes: list[str]) -> None:
    user.two_factor_backup_codes = json.dumps(codes)


def verify_totp_or_backup_code(user: User, code: str, session: Session) -> bool:
    code = code.strip().replace(" ", "")

    if user.two_factor_secret:
        totp = build_totp(user.two_factor_secret)
        if totp.verify(code, valid_window=1):
            return True

    backup_codes = load_backup_codes(user)
    if code in backup_codes:
        backup_codes.remove(code)
        save_backup_codes(user, backup_codes)
        session.add(user)
        session.commit()
        return True

    return False


# --- Dependencies ---

def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        sub = payload.get("sub")
        if sub is None:
            raise credentials_exception
        user_id = int(sub)
    except (JWTError, ValueError):
        raise credentials_exception

    user = session.get(User, user_id)
    if user is None:
        raise credentials_exception

    if user.last_active:
        inactivity_seconds = (datetime.utcnow() - user.last_active).total_seconds()
        if inactivity_seconds > INACTIVITY_TIMEOUT_SECONDS:
            logger.warning(f"Session expired for {user.email} due to inactivity ({inactivity_seconds} seconds)")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired due to inactivity. Please log in again.",
            )

    user.last_active = datetime.utcnow()
    session.commit()
    return user


# --- Routes ---

@router.post("/register", response_model=UserRead)
async def register(user_in: UserCreate, session: Session = Depends(get_session)):
    existing = get_user_by_email(session, user_in.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists.",
        )

    if not meets_password_policy(user_in.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 12 characters with uppercase, lowercase, digit, and special character.",
        )

    user = User(
        email=user_in.email,
        password_hash=get_password_hash(user_in.password),
        role=user_in.role or "patient",
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    try:
        from .smtp_mailer import send_account_created_email
        send_account_created_email(
            to_email=user.email,
            name=user.email.split('@')[0]
        )
    except Exception as e:
        print(f"Failed to send welcome email: {e}")

    return user


@router.post("/login/start", response_model=LoginStartResponse)
async def login_start(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    recaptcha_token: str = Form(None),
    session: Session = Depends(get_session),
):
    remote_ip = request.client.host if request.client else None

    if remote_ip and captcha_service.is_rate_limited(remote_ip):
        logger.warning(f"Rate limited login attempt from {remote_ip}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed attempts. Please try again later."
        )

    if not recaptcha_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CAPTCHA verification required"
        )

    is_valid = await captcha_service.verify_login(recaptcha_token, remote_ip)

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CAPTCHA verification failed. Please try again."
    )

    user = get_user_by_email(session, form_data.username)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.lockout_until and user.lockout_until > datetime.utcnow():
        remaining = (user.lockout_until - datetime.utcnow()).total_seconds() / 60
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account locked due to too many failed attempts. Try again in {int(remaining)} minutes.",
        )

    if not verify_password(form_data.password, user.password_hash):
        user.failed_login_attempts += 1

        if user.failed_login_attempts >= 5:
            user.lockout_until = datetime.utcnow() + timedelta(minutes=15)
            session.commit()
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account locked due to too many failed attempts. Locked for 15 minutes.",
            )

        session.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Password is correct
    user.failed_login_attempts = 0
    user.lockout_until = None
    session.commit()

    if user.two_factor_enabled:
        temp_token = create_temp_2fa_token(user)
        return LoginStartResponse(
            requires_2fa=True,
            temp_token=temp_token,
        )

    user.last_active = datetime.utcnow()
    session.commit()

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role},
        expires_delta=access_token_expires,
    )

    return LoginStartResponse(
        requires_2fa=False,
        access_token=access_token,
        token_type="bearer",
    )


@router.post("/login/verify-2fa", response_model=Token)
async def login_verify_2fa(
    payload: Login2FARequest,
    session: Session = Depends(get_session),
):
    user_id = decode_temp_2fa_token(payload.temp_token)
    user = session.get(User, user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    if not user.two_factor_enabled or not user.two_factor_secret:
        raise HTTPException(status_code=400, detail="2FA is not enabled for this account.")

    if user.lockout_until and user.lockout_until > datetime.utcnow():
        remaining = (user.lockout_until - datetime.utcnow()).total_seconds() / 60
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account locked due to too many failed attempts. Try again in {int(remaining)} minutes.",
        )

    if not verify_totp_or_backup_code(user, payload.code, session):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 5:
            user.lockout_until = datetime.utcnow() + timedelta(minutes=15)
            session.commit()
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account locked due to too many failed attempts. Locked for 15 minutes.",
            )

        session.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid 2FA code.",
        )

    user.failed_login_attempts = 0
    user.lockout_until = None
    user.last_active = datetime.utcnow()
    session.commit()

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role},
        expires_delta=access_token_expires,
    )

    return Token(access_token=access_token, token_type="bearer")


# Backward-compatible old login endpoint now points to login_start behavior
@router.post("/login", response_model=LoginStartResponse)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    recaptcha_token: str = Form(None),
    session: Session = Depends(get_session),
):
    return await login_start(request, form_data, recaptcha_token, session)


@router.get("/2fa/status", response_model=TwoFactorStatusResponse)
def get_two_factor_status(current_user: User = Depends(get_current_user)):
    return TwoFactorStatusResponse(enabled=current_user.two_factor_enabled)


@router.post("/2fa/setup/start", response_model=TwoFactorSetupStartResponse)
def start_two_factor_setup(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    secret = pyotp.random_base32()
    current_user.two_factor_temp_secret = secret
    session.add(current_user)
    session.commit()

    otpauth_url = pyotp.totp.TOTP(secret).provisioning_uri(
        name=current_user.email,
        issuer_name=settings.TOTP_ISSUER_NAME,
    )
    qr_code_base64 = make_qr_code_base64(otpauth_url)

    return TwoFactorSetupStartResponse(
        secret=secret,
        otpauth_url=otpauth_url,
        qr_code_base64=qr_code_base64,
    )


@router.post("/2fa/setup/verify", response_model=BackupCodesResponse)
def verify_two_factor_setup(
    payload: TwoFactorSetupVerifyRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if not current_user.two_factor_temp_secret:
        raise HTTPException(status_code=400, detail="No pending 2FA setup found.")

    totp = build_totp(current_user.two_factor_temp_secret)
    if not totp.verify(payload.code.strip(), valid_window=1):
        raise HTTPException(status_code=400, detail="Invalid authenticator code.")

    current_user.two_factor_secret = current_user.two_factor_temp_secret
    current_user.two_factor_temp_secret = None
    current_user.two_factor_enabled = True

    backup_codes = generate_backup_codes()
    save_backup_codes(current_user, backup_codes)

    session.add(current_user)
    session.commit()

    return BackupCodesResponse(backup_codes=backup_codes)


@router.post("/2fa/disable")
def disable_two_factor(
    payload: TwoFactorDisableRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if not current_user.two_factor_enabled:
        raise HTTPException(status_code=400, detail="2FA is not enabled.")

    if not verify_password(payload.password, current_user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect password.")

    if not current_user.two_factor_secret:
        raise HTTPException(status_code=400, detail="No active 2FA secret found.")

    totp = build_totp(current_user.two_factor_secret)
    if not totp.verify(payload.code.strip(), valid_window=1):
        raise HTTPException(status_code=400, detail="Invalid authenticator code.")

    current_user.two_factor_enabled = False
    current_user.two_factor_secret = None
    current_user.two_factor_temp_secret = None
    current_user.two_factor_backup_codes = None

    session.add(current_user)
    session.commit()

    return {"message": "2FA disabled successfully."}


@router.post("/2fa/backup-codes/regenerate", response_model=BackupCodesResponse)
def regenerate_backup_codes(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if not current_user.two_factor_enabled:
        raise HTTPException(status_code=400, detail="2FA is not enabled.")

    backup_codes = generate_backup_codes()
    save_backup_codes(current_user, backup_codes)
    session.add(current_user)
    session.commit()

    return BackupCodesResponse(backup_codes=backup_codes)

@router.post("/ping")
def ping_session(current_user: User = Depends(get_current_user)):
    """
    Refresh session activity for active users.
    get_current_user already updates last_active.
    """
    return {
        "message": "Session refreshed",
        "last_active": current_user.last_active.isoformat() if current_user.last_active else None,
    }


@router.get("/me", response_model=UserRead)
def read_me(current_user: User = Depends(get_current_user)):
    return current_user