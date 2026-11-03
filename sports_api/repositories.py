from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from .models import Athlete, Result, Sport


class SportRepository:
    def __init__(self, session: Session):
        self.session = session

    def add(self, sport: Sport) -> Sport:
        self.session.add(sport)
        self.session.flush()
        return sport

    def get(self, sport_id: int) -> Sport | None:
        return self.session.get(Sport, sport_id)

    def list_all(self) -> list[Sport]:
        return list(self.session.scalars(select(Sport).order_by(Sport.name)))

    def update(self, sport: Sport, values: dict) -> Sport:
        for field, value in values.items():
            setattr(sport, field, value)
        self.session.flush()
        return sport

    def delete(self, sport: Sport) -> None:
        self.session.delete(sport)
        self.session.flush()


class AthleteRepository:
    def __init__(self, session: Session):
        self.session = session

    def add(self, athlete: Athlete) -> Athlete:
        self.session.add(athlete)
        self.session.flush()
        return athlete

    def get(self, athlete_id: int) -> Athlete | None:
        return self.session.get(Athlete, athlete_id)

    def list_all(self, sport_id: int | None = None, name: str | None = None) -> list[Athlete]:
        statement = select(Athlete).options(joinedload(Athlete.sport)).order_by(Athlete.name)
        if sport_id is not None:
            statement = statement.where(Athlete.sport_id == sport_id)
        if name:
            statement = statement.where(Athlete.name.ilike(f"%{name}%"))
        return list(self.session.scalars(statement))

    def update(self, athlete: Athlete, values: dict) -> Athlete:
        for field, value in values.items():
            setattr(athlete, field, value)
        self.session.flush()
        return athlete

    def delete(self, athlete: Athlete) -> None:
        self.session.delete(athlete)
        self.session.flush()


class ResultRepository:
    def __init__(self, session: Session):
        self.session = session

    def add(self, result: Result) -> Result:
        self.session.add(result)
        self.session.flush()
        return result

    def add_many(self, results: list[Result]) -> list[Result]:
        self.session.add_all(results)
        self.session.flush()
        return results

    def get(self, result_id: int) -> Result | None:
        return self.session.get(Result, result_id)

    def list_for_sport(self, sport_id: int) -> list[Result]:
        statement = (
            select(Result)
            .join(Result.athlete)
            .where(Athlete.sport_id == sport_id)
            .options(joinedload(Result.athlete))
            .order_by(Result.id)
        )
        return list(self.session.scalars(statement))

    def ranking(self, sport_id: int) -> list[Result]:
        statement = (
            select(Result)
            .join(Result.athlete)
            .where(Athlete.sport_id == sport_id)
            .options(joinedload(Result.athlete))
            .order_by(Result.value.asc(), Result.id.asc())
        )
        return list(self.session.scalars(statement))

    def statistics(self, sport_id: int) -> tuple[int, float | None, float | None, float | None]:
        statement = (
            select(
                func.count(Result.id),
                func.avg(Result.value),
                func.min(Result.value),
                func.max(Result.value),
            )
            .join(Result.athlete)
            .where(Athlete.sport_id == sport_id)
        )
        return self.session.execute(statement).one()

    def update(self, result: Result, values: dict) -> Result:
        for field, value in values.items():
            setattr(result, field, value)
        self.session.flush()
        return result

    def delete(self, result: Result) -> None:
        self.session.delete(result)
        self.session.flush()
