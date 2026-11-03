from __future__ import annotations

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
        self.repository = SportRepository(session)

    def create(self, values: dict) -> Sport:
        try:
            sport = self.repository.add(Sport(**values))
            self.session.commit()
            self.session.refresh(sport)
            return sport
        except IntegrityError as exc:
            self.session.rollback()
            raise ResourceConflict("Sport name already exists") from exc

    def get(self, sport_id: int) -> Sport:
        sport = self.repository.get(sport_id)
        if sport is None:
            raise ResourceNotFound("Sport not found")
        return sport

    def list(self) -> list[Sport]:
        return self.repository.list_all()

    def update(self, sport_id: int, values: dict) -> Sport:
        sport = self.get(sport_id)
        try:
            self.repository.update(sport, values)
            self.session.commit()
            self.session.refresh(sport)
            return sport
        except IntegrityError as exc:
            self.session.rollback()
            raise ResourceConflict("Sport name already exists") from exc

    def delete(self, sport_id: int) -> None:
        sport = self.get(sport_id)
        self.repository.delete(sport)
        self.session.commit()


class AthleteService:
    def __init__(self, session: Session):
        self.session = session
        self.sports = SportRepository(session)
        self.repository = AthleteRepository(session)

    def create(self, values: dict) -> Athlete:
        if self.sports.get(values["sport_id"]) is None:
            raise ResourceNotFound("Sport not found")
        try:
            athlete = self.repository.add(Athlete(**values))
            self.session.commit()
            self.session.refresh(athlete)
            return athlete
        except IntegrityError as exc:
            self.session.rollback()
            raise ResourceConflict("Athlete already exists for this sport") from exc

    def get(self, athlete_id: int) -> Athlete:
        athlete = self.repository.get(athlete_id)
        if athlete is None:
            raise ResourceNotFound("Athlete not found")
        return athlete

    def list(self, sport_id: int | None = None, name: str | None = None) -> list[Athlete]:
        if sport_id is not None and self.sports.get(sport_id) is None:
            raise ResourceNotFound("Sport not found")
        return self.repository.list_all(sport_id, name)

    def update(self, athlete_id: int, values: dict) -> Athlete:
        athlete = self.get(athlete_id)
        sport_id = values.get("sport_id")
        if sport_id is not None and self.sports.get(sport_id) is None:
            raise ResourceNotFound("Sport not found")
        try:
            self.repository.update(athlete, values)
            self.session.commit()
            self.session.refresh(athlete)
            return athlete
        except IntegrityError as exc:
            self.session.rollback()
            raise ResourceConflict("Athlete already exists for this sport") from exc

    def delete(self, athlete_id: int) -> None:
        self.repository.delete(self.get(athlete_id))
        self.session.commit()


class ResultService:
    def __init__(self, session: Session):
        self.session = session
        self.sports = SportRepository(session)
        self.athletes = AthleteRepository(session)
        self.repository = ResultRepository(session)

    def create(self, values: dict) -> Result:
        if self.athletes.get(values["athlete_id"]) is None:
            raise ResourceNotFound("Athlete not found")
        try:
            result = self.repository.add(Result(**values))
            self.session.commit()
            self.session.refresh(result)
            return result
        except IntegrityError:
            self.session.rollback()
            raise

    def create_batch(self, items: list[dict]) -> list[Result]:
        athlete_ids = {item["athlete_id"] for item in items}
        missing = [item_id for item_id in athlete_ids if self.athletes.get(item_id) is None]
        if missing:
            raise ResourceNotFound(f"Athlete not found: {missing[0]}")
        try:
            results = self.repository.add_many([Result(**item) for item in items])
            self.session.commit()
            for result in results:
                self.session.refresh(result)
            return results
        except Exception:
            self.session.rollback()
            raise

    def get(self, result_id: int) -> Result:
        result = self.repository.get(result_id)
        if result is None:
            raise ResourceNotFound("Result not found")
        return result

    def update(self, result_id: int, values: dict) -> Result:
        result = self.get(result_id)
        athlete_id = values.get("athlete_id")
        if athlete_id is not None and self.athletes.get(athlete_id) is None:
            raise ResourceNotFound("Athlete not found")
        self.repository.update(result, values)
        self.session.commit()
        self.session.refresh(result)
        return result

    def delete(self, result_id: int) -> None:
        self.repository.delete(self.get(result_id))
        self.session.commit()

    def list_for_sport(self, sport_id: int) -> list[Result]:
        self._require_sport(sport_id)
        return self.repository.list_for_sport(sport_id)

    def ranking(self, sport_id: int) -> list[Result]:
        self._require_sport(sport_id)
        return self.repository.ranking(sport_id)

    def statistics(self, sport_id: int) -> tuple[Sport, int, float | None, float | None, float | None]:
        sport = self._require_sport(sport_id)
        count, average, best, maximum = self.repository.statistics(sport_id)
        return sport, count, average, best, maximum

    def _require_sport(self, sport_id: int) -> Sport:
        sport = self.sports.get(sport_id)
        if sport is None:
            raise ResourceNotFound("Sport not found")
        return sport
