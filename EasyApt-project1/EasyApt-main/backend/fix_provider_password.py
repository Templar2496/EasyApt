import sys
sys.path.insert(0, '/home/mjr0315@students.ad.unt.edu/EasyApt/backend')

from app.database import engine
from app.models import User
from passlib.context import CryptContext
from sqlmodel import Session, select

# Use the SAME password context as auth.py
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def fix_provider_password(email: str, new_password: str):
    """Fix the provider's password with correct hash"""
    hashed_password = pwd_context.hash(new_password)
    
    with Session(engine) as session:
        statement = select(User).where(User.email == email)
        user = session.exec(statement).first()
        
        if not user:
            print(f"❌ User {email} not found!")
            return
        
        user.password_hash = hashed_password
        session.add(user)
        session.commit()
        print(f"✅ Fixed password for {email}")

if __name__ == "__main__":
    fix_provider_password("dr.smith@example.com", "provider123")
    
    print("\n" + "="*50)
    print("Provider password fixed!")
    print("Email: dr.smith@example.com")
    print("Password: provider123")
    print("="*50)
