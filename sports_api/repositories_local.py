from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .models import Athlete, Result, Sport


class SportRepository:
    def __init__(self, session: Session):
        self.session = session

    def get(self, sport_id: int) -> Sport | None:
        return self.session.get(Sport, sport_id)

    def list(self) -> list[Sport]:
        return list(self.session.scalars(select(Sport).order_by(Sport.name)))

    def add(self, sport: Sport) -> Sport:
        self.session.add(sport)
        self.session.commit()
        self.session.refresh(sport)
        return sport

    def update(self, sport_id: int, *, name: str | None = None, discipline: str | None = None) -> Sport | None:
        sport = self.get(sport_id)
        if sport is None:
            return None
        if name is not None:
            sport.name = name
        if discipline is not None:
            sport.discipline = discipline
        self.session.flush()
        return sport

    def delete(self, sport_id: int) -> bool:
        sport = self.get(sport_id)
        if sport is None:
            return False
        self.session.delete(sport)
        self.session.flush()
        return True


class AthleteRepository:
    def __init__(self, session: Session):
        self.session = session

    def get(self, athlete_id: int) -> Athlete | None:
        return self.session.get(Athlete, athlete_id)

    def list(self, sport_id: int | None = None, name: str | None = None) -> list[Athlete]:
        statement = select(Athlete)
        if sport_id is not None:
            statement = statement.where(Athlete.sport_id == sport_id)
        if name:
            statement = statement.where(Athlete.name.ilike(f"%{name}%"))
        return list(self.session.scalars(statement.order_by(Athlete.name)))

    def add(self, athlete: Athlete) -> Athlete:
        self.session.add(athlete)
        self.session.commit()
        self.session.refresh(athlete)
        return athlete

    def update(self, athlete_id: int, *, name: str | None = None, category: str | None = None, sport_id: int | None = None) -> Athlete | None:
        athlete = self.get(athlete_id)
        if athlete is None:
            return None
        if name is not None:
            athlete.name = name
        if category is not None:
            athlete.category = category
        if sport_id is not None:
            athlete.sport_id = sport_id
        self.session.flush()
        return athlete

    def delete(self, athlete_id: int) -> bool:
        athlete = self.get(athlete_id)
        if athlete is None:
            return False
        self.session.delete(athlete)
        self.session.flush()
        return True


class ResultRepository:
    def __init__(self, session: Session):
        self.session = session

    def get(self, result_id: int) -> Result | None:
        return self.session.get(Result, result_id)

    def add(self, result: Result) -> Result:
        self.session.add(result)
        self.session.commit()
        self.session.refresh(result)
        return result

    def list_for_sport(self, sport_id: int) -> list[Result]:
        statement = select(Result).join(Athlete).where(Athlete.sport_id == sport_id)
        return list(self.session.scalars(statement.order_by(Result.value)))

    def ranking(self, sport_id: int) -> list[tuple[Result, Athlete]]:
        statement = (select(Result, Athlete)
            .join(Athlete, Result.athlete_id == Athlete.id)
            .where(Athlete.sport_id == sport_id)
            .order_by(Result.value.asc()))
        return list(self.session.execute(statement).all())

    def statistics(self, sport_id: int) -> tuple[int, float | None, float | None, float | None]:
        statement = (select(func.count(Result.id), func.avg(Result.value), func.min(Result.value), func.max(Result.value))
            .join(Athlete, Result.athlete_id == Athlete.id)
            .where(Athlete.sport_id == sport_id))
        return self.session.execute(statement).one()
