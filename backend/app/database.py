from sqlmodel import SQLModel, create_engine, Session
from .config import settings

# For Postgres, connect_args can stay empty
connect_args = {}
engine = create_engine(
    settings.DATABASE_URL,
    echo=True,
    connect_args=connect_args,
)


def init_db():
    SQLModel.metadata.create_all(engine)


def get_session():
    """Dependency to get a database session for each request."""
    with Session(engine) as session:
        yield session
