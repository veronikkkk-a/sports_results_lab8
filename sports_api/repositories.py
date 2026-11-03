"""Lab 8 API adapters over the Lab 7 repository implementations."""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .models import Athlete, Result, Sport, USE_LAB7_PERSISTENCE

if USE_LAB7_PERSISTENCE:
    from sports_streaming.repositories import (
        AthleteRepository as Lab7AthleteRepository,
        ResultRepository as Lab7ResultRepository,
        SportRepository as Lab7SportRepository,
    )

    class SportRepository(Lab7SportRepository):
        def list(self) -> list[Sport]:
            return self.list_all()

        def add(self, sport: Sport) -> Sport:
            item = super().add(sport.name, sport.discipline)
            self.session.commit()
            self.session.refresh(item)
            return item

    class AthleteRepository(Lab7AthleteRepository):
        def list(self, sport_id: int | None = None, name: str | None = None) -> list[Athlete]:
            athletes = self.list_all(sport_id)
            if name:
                query = name.casefold()
                athletes = [athlete for athlete in athletes if query in athlete.name.casefold()]
            return athletes

        def add(self, athlete: Athlete) -> Athlete:
            item = super().add(athlete.name, athlete.category, athlete.sport_id)
            self.session.commit()
            self.session.refresh(item)
            return item

    class ResultRepository(Lab7ResultRepository):
        def add(self, result: Result) -> Result:
            item = super().add(
                result.athlete_id,
                result.value,
                result.competition_name,
                result.competition_date,
            )
            self.session.commit()
            self.session.refresh(item)
            return item

        def list_for_sport(self, sport_id: int) -> list[Result]:
            sport = self.session.get(Sport, sport_id)
            if sport is None:
                return []
            return self.list_all(sport.name)

        def ranking(self, sport_id: int) -> list[tuple[Result, Athlete]]:
            sport = self.session.get(Sport, sport_id)
            if sport is None:
                return []
            return [(result, result.athlete) for result in super().ranking(sport.name)]

        def statistics(self, sport_id: int) -> tuple[int, float | None, float | None]:
            rows = self.list_for_sport(sport_id)
            if not rows:
                return 0, None, None
            values = [row.value for row in rows]
            return len(values), sum(values) / len(values), min(values)
else:
    from .repositories_local import AthleteRepository, ResultRepository, SportRepository
