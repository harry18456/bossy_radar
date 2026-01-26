from sqlmodel import create_engine, Session
from app.core.config import settings

# access_token is just an example of what might be in settings, here we just use DATABASE_URL
# connect_args={"check_same_thread": False} is needed for SQLite
engine = create_engine(settings.DATABASE_URL, echo=False, connect_args={"check_same_thread": False})
archive_engine = create_engine(settings.ARCHIVE_DATABASE_URL, echo=False, connect_args={"check_same_thread": False})

def get_session():
    with Session(engine) as session:
        yield session

def get_archive_session():
    with Session(archive_engine) as session:
        yield session
