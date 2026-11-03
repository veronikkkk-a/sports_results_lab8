"""Use Lab 7's SQLAlchemy mappings when the previous project is available."""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LAB7_SRC = PROJECT_ROOT.parent / "lab7" / "src"
if LAB7_SRC.is_dir() and str(LAB7_SRC) not in sys.path:
    sys.path.insert(0, str(LAB7_SRC))

try:
    from sports_streaming.db_models import Athlete, Base, Result, Sport
    USE_LAB7_PERSISTENCE = True
except ModuleNotFoundError:
    from sqlalchemy import CheckConstraint, Date, Float, ForeignKey, String, UniqueConstraint
    from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

    USE_LAB7_PERSISTENCE = False

    class Base(DeclarativeBase):
        pass

    class Sport(Base):
        __tablename__ = "sports"
        __table_args__ = (UniqueConstraint("name", name="uq_sports_name"),)
        id: Mapped[int] = mapped_column(primary_key=True)
        name: Mapped[str] = mapped_column(String(80), nullable=False)
        discipline: Mapped[str] = mapped_column(String(80), nullable=False, default="general")
        athletes: Mapped[list[Athlete]] = relationship(back_populates="sport", cascade="all, delete-orphan")

    class Athlete(Base):
        __tablename__ = "athletes"
        __table_args__ = (UniqueConstraint("sport_id", "name", name="uq_athletes_sport_name"),)
        id: Mapped[int] = mapped_column(primary_key=True)
        name: Mapped[str] = mapped_column(String(120), nullable=False)
        category: Mapped[str] = mapped_column(String(80), nullable=False)
        sport_id: Mapped[int] = mapped_column(ForeignKey("sports.id", ondelete="CASCADE"), nullable=False)
        sport: Mapped[Sport] = relationship(back_populates="athletes")
        results: Mapped[list[Result]] = relationship(back_populates="athlete", cascade="all, delete-orphan")

    class Result(Base):
        __tablename__ = "results"
        __table_args__ = (CheckConstraint("value >= 0", name="ck_results_value_nonnegative"),)
        id: Mapped[int] = mapped_column(primary_key=True)
        athlete_id: Mapped[int] = mapped_column(ForeignKey("athletes.id", ondelete="CASCADE"), nullable=False)
        value: Mapped[float] = mapped_column(Float, nullable=False)
        competition_name: Mapped[str] = mapped_column(String(120), nullable=False, default="Training")
        competition_date: Mapped[date | None] = mapped_column(Date, nullable=True)
        athlete: Mapped[Athlete] = relationship(back_populates="results")
