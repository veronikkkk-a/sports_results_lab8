"""Transactional batch persistence service."""
from __future__ import annotations
from collections.abc import Iterable, Mapping
from sqlalchemy.orm import Session
from sports_streaming.db_models import Athlete, Result
from sports_streaming.models import SportsResult

def save_result_batch(session: Session, records: Iterable[SportsResult], athlete_ids: Mapping[str | tuple[str, str], int], competition_name: str = "Imported results") -> list[Result]:
    """Persist the full batch or roll back every write if one row is invalid."""
    created: list[Result] = []
    try:
        for record in records:
            if record.result < 0:
                raise ValueError(f"Result must be non-negative: {record.result}")
            athlete_key = (record.sport, record.athlete)
            athlete_id = athlete_ids.get(athlete_key, athlete_ids.get(record.athlete))
            if athlete_id is None:
                raise ValueError(f"Athlete is not registered: {record.athlete} ({record.sport})")
            athlete = session.get(Athlete, athlete_id)
            if athlete is None:
                raise ValueError(f"Athlete id does not exist: {athlete_id}")
            created.append(Result(athlete_id=athlete.id, value=record.result, competition_name=competition_name, competition_date=record.timestamp.date()))
            session.add(created[-1])
        session.flush()
        session.commit()
        return created
    except Exception:
        session.rollback()
        raise


def persist_imported_results(session: Session, records: Iterable[SportsResult], competition_name: str = "CSV import") -> list[Result]:
    """Register missing sports/athletes, then atomically persist the imported result batch."""
    from sports_streaming.repositories import AthleteRepository, SportRepository
    rows = list(records)
    if not rows:
        return []
    sport_repo = SportRepository(session)
    athlete_repo = AthleteRepository(session)
    athlete_ids: dict[tuple[str, str], int] = {}
    for row in rows:
        sport = sport_repo.get_by_name(row.sport)
        if sport is None:
            sport = sport_repo.add(row.sport)
        athlete = next((item for item in athlete_repo.list_all(sport.id) if item.name == row.athlete), None)
        if athlete is None:
            athlete = athlete_repo.add(row.athlete, row.category, sport.id)
        athlete_ids[(row.sport, row.athlete)] = athlete.id
    session.commit()
    return save_result_batch(session, rows, athlete_ids, competition_name)

