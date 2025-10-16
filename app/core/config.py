import os
from dotenv import load_dotenv
load_dotenv()

DB_DSN = os.getenv("DB_DSN", "postgresql://app:app@localhost:5432/appdb")
SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")
