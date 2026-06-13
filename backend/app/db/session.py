from sqlalchemy import event
from sqlmodel import Session, create_engine

from app.core.config import settings

# access_token is just an example of what might be in settings, here we just use DATABASE_URL
# connect_args={"check_same_thread": False} is needed for SQLite
engine = create_engine(
    settings.DATABASE_URL, echo=False, connect_args={"check_same_thread": False}
)
archive_engine = create_engine(
    settings.ARCHIVE_DATABASE_URL, echo=False, connect_args={"check_same_thread": False}
)


def _configure_sqlite(dbapi_connection, connection_record):
    """Enforce runtime PRAGMAs on every SQLite connection (BACKEND_AUDIT M6/M7).

    - journal_mode=WAL lets readers and the writer run concurrently instead of
      blocking, so a long CLI sync no longer 500s the API with SQLITE_BUSY.
    - busy_timeout makes a contending writer wait rather than fail immediately.
    - foreign_keys=ON enforces the company_code references that were declared
      but never enforced.
    """
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


event.listens_for(engine, "connect")(_configure_sqlite)
event.listens_for(archive_engine, "connect")(_configure_sqlite)


def get_session():
    with Session(engine) as session:
        yield session


def get_archive_session():
    with Session(archive_engine) as session:
        yield session
