import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, SQLModel
from sqlmodel.pool import StaticPool
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.database import get_session
from app.models import User, Provider, Appointment
from app.auth import get_password_hash

# Test database engine (in-memory SQLite)
@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session
    
    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

@pytest.fixture(name="test_patient")
def test_patient_fixture(session: Session):
    """Create a test patient user"""
    user = User(
        email="testpatient@example.com",
        password_hash=get_password_hash("TestPassword123!"),
        role="patient"
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

@pytest.fixture(name="test_provider")
def test_provider_fixture(session: Session):
    """Create a test provider user and provider profile"""
    # Create provider user
    user = User(
        email="testprovider@example.com",
        password_hash=get_password_hash("ProviderPass123!"),
        role="provider"
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    
    # Create provider profile linked to user
    provider = Provider(
        user_id=user.id,
        name="Dr. Test Provider",
        specialty="General Practice"
    )
    session.add(provider)
    session.commit()
    session.refresh(provider)
    
    return {"user": user, "provider": provider}
