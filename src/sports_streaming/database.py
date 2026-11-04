from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session

def make_engine(url: str = "sqlite:///sports_results.db", echo: bool = False) -> Engine:
    engine = create_engine(url, echo=echo)
    if url.startswith("sqlite"):
        @event.listens_for(engine, "connect")
        def enable_foreign_keys(dbapi_connection, record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
    return engine

def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False)

# Глобальний екземпляр engine для роботи застосунку та FastAPI
engine = make_engine()

# Готова фабрика сесій, яку імпортують залежності (dependencies.py)
SessionLocal = make_session_factory(engine)