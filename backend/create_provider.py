import sys
sys.path.insert(0, '/home/mjr0315@students.ad.unt.edu/EasyApt/backend')

from app.database import engine
from app.models import User, Provider
from passlib.context import CryptContext
from sqlmodel import Session, select

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_provider(email: str, password: str, name: str):
    """Create a provider account"""
    hashed_password = pwd_context.hash(password)
    
    with Session(engine) as session:
        # Check if user already exists
        statement = select(User).where(User.email == email)
        existing = session.exec(statement).first()
        
        if existing:
            print(f"User {email} already exists. Updating to provider role...")
            existing.role = "provider"
            session.add(existing)
            session.commit()
            print(f"✅ Updated {email} to provider role!")
        else:
            # Create new provider user
            new_user = User(
                email=email,
                password_hash=hashed_password,
                role="provider"
            )
            session.add(new_user)
            session.commit()
            print(f"✅ Created new provider user: {email}")
        
        # Check if provider profile exists
        provider_statement = select(Provider).where(Provider.name == name)
        provider_profile = session.exec(provider_statement).first()
        
        if not provider_profile:
            provider_profile = Provider(
                name=name,
                specialty="General Practice"
            )
            session.add(provider_profile)
            session.commit()
            print(f"✅ Created provider profile for {name}")
        else:
            print(f"✅ Provider profile already exists for {name}")

if __name__ == "__main__":
    create_provider(
        email="dr.smith@example.com",
        password="provider123",
        name="Dr. Sarah Smith"
    )
    
    print("\n" + "="*50)
    print("Provider account ready!")
    print("Email: dr.smith@example.com")
    print("Password: provider123")
    print("="*50)
    print("\nNow login and go to:")
    print("http://theboys-web.eng.unt.edu/provider-dashboard.html")
