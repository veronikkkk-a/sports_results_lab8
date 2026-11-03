from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .models import Athlete, Result, Sport
from .repositories import AthleteRepository, ResultRepository, SportRepository


class ResourceNotFound(Exception):
    pass


class ResourceConflict(Exception):
    pass


class SportService:
    def __init__(self, session: Session):
        self.session = session
        self.sports = SportRepository(session)

    def create(self, name: str, discipline: str) -> Sport:
        try:
            return self.sports.add(Sport(name=name, discipline=discipline))
        except IntegrityError as exc:
            self.session.rollback()
            raise ResourceConflict("Sport name already exists") from exc

    def list(self) -> list[Sport]:
        return self.sports.list()

    def get(self, sport_id: int) -> Sport:
        sport = self.sports.get(sport_id)
        if sport is None:
            raise ResourceNotFound("Sport not found")
        return sport

    def update(self, sport_id: int, updates: dict) -> Sport:
        try:
            sport = self.sports.update(sport_id, **updates)
            if sport is None:
                raise ResourceNotFound("Sport not found")
            self.session.commit()
            self.session.refresh(sport)
            return sport
        except ResourceNotFound:
            raise
        except IntegrityError as exc:
            self.session.rollback()
            raise ResourceConflict("Sport name already exists") from exc

    def delete(self, sport_id: int) -> None:
        if not self.sports.delete(sport_id):
            raise ResourceNotFound("Sport not found")
        self.session.commit()


class AthleteService:
    def __init__(self, session: Session):
        self.session = session
        self.sports = SportRepository(session)
        self.athletes = AthleteRepository(session)

    def create(self, name: str, category: str, sport_id: int) -> Athlete:
        if self.sports.get(sport_id) is None:
            raise ResourceNotFound("Sport not found")
        try:
            return self.athletes.add(Athlete(name=name, category=category, sport_id=sport_id))
        except IntegrityError as exc:
            self.session.rollback()
            raise ResourceConflict("Athlete already exists for this sport") from exc

    def list(self, sport_id: int | None = None, name: str | None = None) -> list[Athlete]:
        return self.athletes.list(sport_id, name)

    def get(self, athlete_id: int) -> Athlete:
        athlete = self.athletes.get(athlete_id)
        if athlete is None:
            raise ResourceNotFound("Athlete not found")
        return athlete

    def update(self, athlete_id: int, updates: dict) -> Athlete:
        sport_id = updates.get("sport_id")
        if sport_id is not None and self.sports.get(sport_id) is None:
            raise ResourceNotFound("Sport not found")
        try:
            athlete = self.athletes.update(athlete_id, **updates)
            if athlete is None:
                raise ResourceNotFound("Athlete not found")
            self.session.commit()
            self.session.refresh(athlete)
            return athlete
        except ResourceNotFound:
            raise
        except IntegrityError as exc:
            self.session.rollback()
            raise ResourceConflict("Athlete already exists for this sport") from exc

    def delete(self, athlete_id: int) -> None:
        if not self.athletes.delete(athlete_id):
            raise ResourceNotFound("Athlete not found")
        self.session.commit()


class ResultService:
    def __init__(self, session: Session):
        self.session = session
        self.sports = SportRepository(session)
        self.athletes = AthleteRepository(session)
        self.results = ResultRepository(session)

    def create(self, values: dict) -> Result:
        if self.athletes.get(values["athlete_id"]) is None:
            raise ResourceNotFound("Athlete not found")
        return self.results.add(Result(**values))

    def update(self, result_id: int, updates: dict) -> Result:
        result = self.results.get(result_id)
        if result is None:
            raise ResourceNotFound("Result not found")
        athlete_id = updates.get("athlete_id")
        if athlete_id is not None and self.athletes.get(athlete_id) is None:
            raise ResourceNotFound("Athlete not found")
        for field, value in updates.items():
            setattr(result, field, value)
        self.session.commit()
        self.session.refresh(result)
        return result

    def delete(self, result_id: int) -> None:
        result = self.results.get(result_id)
        if result is None:
            raise ResourceNotFound("Result not found")
        self.session.delete(result)
        self.session.commit()

    def list_for_sport(self, sport_id: int) -> list[Result]:
        self._require_sport(sport_id)
        return self.results.list_for_sport(sport_id)

    def ranking(self, sport_id: int) -> list[tuple[Result, Athlete]]:
        self._require_sport(sport_id)
        return self.results.ranking(sport_id)

    def statistics(self, sport_id: int) -> tuple[Sport, int, float | None, float | None, float | None]:
        sport = self._require_sport(sport_id)
        count, average, best, maximum = self.results.statistics(sport_id)
        return sport, count, average, best, maximum

    def _require_sport(self, sport_id: int) -> Sport:
        sport = self.sports.get(sport_id)
        if sport is None:
            raise ResourceNotFound("Sport not found")
        return sport
