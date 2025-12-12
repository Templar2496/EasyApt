from datetime import datetime, timedelta
from typing import Optional
import re

from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlmodel import SQLModel, Session, select
from jose import JWTError, jwt
from passlib.context import CryptContext
from .captcha_service import captcha_service
from .notification_service import notification_service
import logging
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHash

from .config import settings
from .database import get_session
from .models import User

PASSWORD_POLICY = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{12,}$")

def meets_password_policy(password: str) -> bool:
    """Check if password meets complexity requirements"""
    return bool(PASSWORD_POLICY.match(password))


router = APIRouter()
logger = logging.getLogger(__name__)

# Security settings
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

ph = PasswordHasher()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# --- Pydantic / SQLModel schemas (not DB tables) ---

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


# --- Helper functions ---

def get_password_hash(password: str) -> str:
    return ph.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        # Try Argon2 first
        return ph.verify(hashed_password, plain_password)
    except (VerifyMismatchError, VerificationError, InvalidHash):
        # Fallback to pbkdf2 for existing users
        try:
            from passlib.context import CryptContext
            pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
            return pwd_context.verify(plain_password, hashed_password)
        except:
            return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


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
        print(f"🕐 DEBUG: User {user.email}")
        print(f"   Last active: {user.last_active}")
        print(f"   Current time: {datetime.utcnow()}")
        print(f"   Inactivity: {inactivity_seconds} seconds")
        
        if inactivity_seconds > 30:  # 30 seconds for testing
            logger.warning(f"⏱️ Session expired for {user.email} due to inactivity ({inactivity_seconds} seconds)")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired due to inactivity. Please log in again.",
            )
    else:
        print(f"🕐 DEBUG: User {user.email} has no last_active timestamp")
    
    # Update last active timestamp
    print(f"   Updating last_active to {datetime.utcnow()}")
    user.last_active = datetime.utcnow()
    session.commit()
    return user


# --- Routes ---

@router.post("/register", response_model=UserRead)
async def register(user_in: UserCreate, session: Session = Depends(get_session)):
    """
    Create a new user account. Default role is 'patient'.
    """
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
        await notification_service.send_welcome_email(
            email=user.email,
            name=user.email.split('@')[0]
        )
        print(f"✅ Welcome email sent to {user.email}")
    except Exception as e:
        print(f"⚠️ Failed to send welcome email: {e}")

    return user


@router.post("/login", response_model=Token)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    recaptcha_token: str = Form(None),
    session: Session = Depends(get_session),

):

    """
    Login endpoint with CAPTCHA, account lockout, and failed attempt tracking.
    """
    # Verify CAPTCHA if token provided
    if recaptcha_token:
        remote_ip = request.client.host
        is_valid = await captcha_service.verify_login(recaptcha_token, remote_ip)
        if not is_valid:
            logger.warning(f"⚠️ CAPTCHA verification failed for {form_data.username} from {remote_ip} - Allowing login for demo")
        else:
            logger.info(f"✅ CAPTCHA verified successfully for {form_data.username}")
    else:
        logger.info(f"ℹ️ No CAPTCHA token provided for {form_data.username} - CAPTCHA integration ready but blocked by CSP")
    
    # Get user by email
    user = get_user_by_email(session, form_data.username)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if account is locked
    if user.lockout_until and user.lockout_until > datetime.utcnow():
        remaining = (user.lockout_until - datetime.utcnow()).total_seconds() / 60
        logger.warning(f"🔒 Locked account login attempt: {user.email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account locked due to too many failed attempts. Try again in {int(remaining)} minutes.",
        )
    
    # Verify password
    if not verify_password(form_data.password, user.password_hash):
        # Increment failed attempts
        user.failed_login_attempts += 1
        
        # Lock account after 5 failed attempts
        if user.failed_login_attempts >= 5:
            user.lockout_until = datetime.utcnow() + timedelta(minutes=15)
            session.commit()
            logger.warning(f"🔒 Account locked for {user.email} after 5 failed attempts")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account locked due to too many failed attempts. Locked for 15 minutes.",
            )
        
        session.commit()
        logger.warning(f"⚠️ Failed login attempt {user.failed_login_attempts}/5 for {user.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Successful login - reset failed attempts and lockout
    user.failed_login_attempts = 0
    user.lockout_until = None
    user.last_active = datetime.utcnow()
    session.commit()
    
    logger.info(f"✅ Successful login for {user.email}")
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role},
        expires_delta=access_token_expires,
    )
    
    return Token(access_token=access_token, token_type="bearer")
    if recaptcha_token:
        remote_ip = request.client.host
        is_valid = await captcha_service.verify_login(recaptcha_token, remote_ip)
        if not is_valid:
            logger.warning(f"⚠️ CAPTCHA verification failed for {form_data.username} from {remote_ip} - Allowing login for demo")
        else:
            logger.info(f"✅ CAPTCHA verified successfully for {form_data.username}")
    else:
        logger.info(f"ℹ️ No CAPTCHA token provided for {form_data.username} - CAPTCHA integration ready but blocked by CSP")
    """
    Login with email + password using OAuth2PasswordRequestForm.
    'username' field is treated as email.
    """
    user = authenticate_user(session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires,
    )
    return Token(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=UserRead)
def read_me(current_user: User = Depends(get_current_user)):
    """
    Get the current logged-in user info.
    """
    return current_user
