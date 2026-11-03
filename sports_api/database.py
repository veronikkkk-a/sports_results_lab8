import os
from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from .models import Base, PROJECT_ROOT, USE_LAB7_PERSISTENCE

PREVIOUS_LAB_DB = PROJECT_ROOT.parent / "lab7" / "sports_results.db"
DEFAULT_DB = PREVIOUS_LAB_DB if PREVIOUS_LAB_DB.exists() else PROJECT_ROOT / "sports_results.db"
DATABASE_URL = os.getenv("SPORTS_DB_URL", f"sqlite:///{DEFAULT_DB.as_posix()}")
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)

if DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def enable_foreign_keys(dbapi_connection, _record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

if USE_LAB7_PERSISTENCE:
    from sports_streaming.database import make_session_factory
    SessionLocal = make_session_factory(engine)
else:
    SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
