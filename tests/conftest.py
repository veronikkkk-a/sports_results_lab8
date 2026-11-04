from datetime import datetime
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sports_streaming.db_models import Base
from sports_streaming.repositories import SportRepository, AthleteRepository

@pytest.fixture
def engine():
    engine = create_engine("sqlite+pysqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    @event.listens_for(engine, "connect")
    def fk_on(dbapi_connection, _):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()

@pytest.fixture
def session(engine):
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory() as session:
        yield session
        session.rollback()

# Додаємо аліас db_session для сумісності з тестами endpoints
@pytest.fixture
def db_session(session):
    return session

@pytest.fixture
def seed(session):
    sport = SportRepository(session).add("Swimming", "Aquatics")
    athlete = AthleteRepository(session).add("Anna Koval", "Junior", sport.id)
    session.commit()
    return sport, athlete