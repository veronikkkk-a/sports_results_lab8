from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from sports_streaming.database import SessionLocal


def get_session() -> Generator[Session, None, None]:
    """
    FastAPI dependency для отримання та автоматичного
    закриття сесії бази даних SQLite після завершення запиту.
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


# Створюємо аліас, щоб код, який шукає get_db_session, теж працював без помилок
get_db_session = get_session

# Зручний аліас типу для використання у REST Endpoints
SessionDep = Annotated[Session, Depends(get_session)]