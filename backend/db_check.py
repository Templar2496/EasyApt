import os
from pathlib import Path

from sqlalchemy import create_engine, text

# load .env manually for this quick test
env_path = Path("backend/.env")
db_url = None
for line in env_path.read_text().splitlines():
    if line.startswith("DB_URL="):
        db_url = line.split("=", 1)[1].strip()

assert db_url, "DB_URL not found in backend/.env"
engine = create_engine(db_url, pool_pre_ping=True)

with engine.connect() as conn:
    version = conn.execute(text("select version();")).scalar()
    print("✅ Connected to:", version)
