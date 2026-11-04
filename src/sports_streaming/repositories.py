"""Repository Pattern around SQLAlchemy persistence and a DB-API query."""
from __future__ import annotations
import sqlite3
from collections.abc import Sequence
from sqlalchemy import Engine, func, select
from sqlalchemy.orm import Session, joinedload
from sports_streaming.db_models import Athlete, Result, Sport
from sports_streaming.models import SportsResult

class SportRepository:
    def __init__(self, session: Session): self.session = session
    def add(self, name: str, discipline: str = "general") -> Sport:
        item = Sport(name=name, discipline=discipline); self.session.add(item); self.session.flush(); return item
    def get(self, sport_id: int) -> Sport | None: return self.session.get(Sport, sport_id)
    def get_by_name(self, name: str) -> Sport | None: return self.session.scalar(select(Sport).where(Sport.name == name))
    def list_all(self) -> list[Sport]: return list(self.session.scalars(select(Sport).order_by(Sport.name)))
    def update(self, sport_id: int, *, name: str | None = None, discipline: str | None = None) -> Sport | None:
        item = self.get(sport_id)
        if item is None: return None
        if name is not None: item.name = name
        if discipline is not None: item.discipline = discipline
        self.session.flush(); return item
    def delete(self, sport_id: int) -> bool:
        item = self.get(sport_id)
        if item is None: return False
        self.session.delete(item); self.session.flush(); return True

class AthleteRepository:
    def __init__(self, session: Session): self.session = session
    def add(self, name: str, category: str, sport_id: int) -> Athlete:
        item = Athlete(name=name, category=category, sport_id=sport_id); self.session.add(item); self.session.flush(); return item
    def get(self, athlete_id: int) -> Athlete | None: return self.session.get(Athlete, athlete_id)
    def list_all(self, sport_id: int | None = None) -> list[Athlete]:
        stmt = select(Athlete).options(joinedload(Athlete.sport)).order_by(Athlete.name)
        if sport_id is not None: stmt = stmt.where(Athlete.sport_id == sport_id)
        return list(self.session.scalars(stmt))
    def update(self, athlete_id: int, *, name: str | None = None, category: str | None = None, sport_id: int | None = None) -> Athlete | None:
        item = self.get(athlete_id)
        if item is None: return None
        if name is not None: item.name = name
        if category is not None: item.category = category
        if sport_id is not None: item.sport_id = sport_id
        self.session.flush(); return item
    def delete(self, athlete_id: int) -> bool:
        item = self.get(athlete_id)
        if item is None: return False
        self.session.delete(item); self.session.flush(); return True

class ResultRepository:
    def __init__(self, session: Session): self.session = session
    def add(self, athlete_id: int, value: float, competition_name: str = "Training", competition_date=None) -> Result:
        item = Result(athlete_id=athlete_id, value=value, competition_name=competition_name, competition_date=competition_date); self.session.add(item); self.session.flush(); return item
    def get(self, result_id: int) -> Result | None: return self.session.get(Result, result_id)
    def list_all(self, sport: str | None = None) -> list[Result]:
        stmt = select(Result).join(Result.athlete).join(Athlete.sport).options(joinedload(Result.athlete).joinedload(Athlete.sport)).order_by(Result.id)
        if sport is not None: stmt = stmt.where(Sport.name == sport)
        return list(self.session.scalars(stmt))
    def update(self, result_id: int, *, value: float | None = None, competition_name: str | None = None) -> Result | None:
        item = self.get(result_id)
        if item is None: return None
        if value is not None: item.value = value
        if competition_name is not None: item.competition_name = competition_name
        self.session.flush(); return item
    def delete(self, result_id: int) -> bool:
        item = self.get(result_id)
        if item is None: return False
        self.session.delete(item); self.session.flush(); return True
    def average(self, sport: str) -> float | None:
        stmt = select(func.avg(Result.value)).join(Result.athlete).join(Athlete.sport).where(Sport.name == sport)
        return self.session.scalar(stmt)
    def best(self, sport: str) -> Result | None:
        stmt = select(Result).join(Result.athlete).join(Athlete.sport).where(Sport.name == sport).order_by(Result.value.asc(), Result.id.asc()).limit(1)
        return self.session.scalar(stmt)
    def maximum(self, sport: str) -> float | None:
        """Return MAX(value), useful for sports where a larger score is better."""
        stmt = select(func.max(Result.value)).join(Result.athlete).join(Athlete.sport).where(Sport.name == sport)
        return self.session.scalar(stmt)
    def ranking(self, sport: str) -> list[Result]:
        stmt = select(Result).join(Result.athlete).join(Athlete.sport).options(joinedload(Result.athlete)).where(Sport.name == sport).order_by(Result.value.asc(), Result.id.asc())
        return list(self.session.scalars(stmt))

def filter_results_dbapi(engine: Engine, sport: str) -> list[dict[str, object]]:
    """Demonstrate Python DB-API + SQLite qmark parameter binding."""
    connection = engine.raw_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("""SELECT r.id, a.name AS athlete, s.name AS sport, r.value, a.category, r.competition_name
                         FROM results AS r JOIN athletes AS a ON a.id = r.athlete_id
                         JOIN sports AS s ON s.id = a.sport_id WHERE s.name = ? ORDER BY r.value ASC""", (sport,))
        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    finally:
        connection.close()
