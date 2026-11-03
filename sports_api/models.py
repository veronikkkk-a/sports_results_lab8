from datetime import date
from sqlalchemy import Date, Float, ForeignKey, String, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base

class Sport(Base):
    __tablename__ = "sports"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    discipline: Mapped[str] = mapped_column(String(80), nullable=False)
    athletes: Mapped[list["Athlete"]] = relationship(
        back_populates="sport", cascade="all, delete-orphan"
    )

class Athlete(Base):
    __tablename__ = "athletes"
    __table_args__ = (UniqueConstraint("sport_id", "name", name="uq_athlete_sport_name"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    sport_id: Mapped[int] = mapped_column(ForeignKey("sports.id", ondelete="CASCADE"), nullable=False)
    sport: Mapped["Sport"] = relationship(back_populates="athletes")
    results: Mapped[list["Result"]] = relationship(
        back_populates="athlete", cascade="all, delete-orphan"
    )

class Result(Base):
    __tablename__ = "results"
    __table_args__ = (CheckConstraint("value >= 0", name="ck_result_nonnegative"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    athlete_id: Mapped[int] = mapped_column(ForeignKey("athletes.id", ondelete="CASCADE"), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    competition_name: Mapped[str] = mapped_column(String(120), nullable=False)
    competition_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    athlete: Mapped["Athlete"] = relationship(back_populates="results")
