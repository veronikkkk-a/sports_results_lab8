from datetime import datetime
import pytest
from sqlalchemy.exc import IntegrityError
from sports_streaming.db_models import Athlete, Result, Sport
from sports_streaming.repositories import AthleteRepository, ResultRepository, SportRepository, filter_results_dbapi
from sports_streaming.persistence_service import save_result_batch
from sports_streaming.models import SportsResult

def test_sport_crud(session):
    repo = SportRepository(session); item = repo.add("Tennis", "Racket")
    assert repo.get(item.id).name == "Tennis"
    assert repo.update(item.id, name="Table tennis").name == "Table tennis"
    assert repo.delete(item.id) is True and repo.get(item.id) is None

def test_athlete_crud(session, seed):
    sport, athlete = seed; repo = AthleteRepository(session)
    assert repo.get(athlete.id).name == "Anna Koval"
    assert repo.list_all(sport.id)[0].sport.name == "Swimming"
    assert repo.update(athlete.id, category="Senior").category == "Senior"
    assert repo.delete(athlete.id) is True and repo.get(athlete.id) is None

def test_result_crud(session, seed):
    _, athlete = seed; repo = ResultRepository(session); item = repo.add(athlete.id, 52.4, "City Cup")
    assert repo.get(item.id).value == 52.4
    assert repo.update(item.id, value=51.9, competition_name="Final").value == 51.9
    assert repo.delete(item.id) is True and repo.get(item.id) is None

def test_foreign_key_and_check_constraints(session, seed):
    _, athlete = seed; session.add(Result(athlete_id=athlete.id, value=-1, competition_name="Invalid"))
    with pytest.raises(IntegrityError): session.flush()
    session.rollback()
    session.add(Result(athlete_id=999999, value=10.0, competition_name="Missing athlete"))
    with pytest.raises(IntegrityError): session.flush()
    session.rollback()

def test_parameterized_dbapi_filter_and_sport_isolation(session, engine, seed):
    sport, athlete = seed; ResultRepository(session).add(athlete.id, 54.2, "Open")
    other = SportRepository(session).add("Cycling", "Road"); cyclist = AthleteRepository(session).add("Bohdan", "Elite", other.id)
    ResultRepository(session).add(cyclist.id, 210.0, "Tour")
    found = filter_results_dbapi(engine, "Swimming")
    assert len(found) == 1 and found[0]["athlete"] == "Anna Koval"
    assert filter_results_dbapi(engine, "Swimming' OR 1=1 --") == []

def test_best_average_and_ranking(session, seed):
    _, athlete = seed; repo = ResultRepository(session)
    repo.add(athlete.id, 55.0, "Meet 1"); repo.add(athlete.id, 52.0, "Meet 2"); repo.add(athlete.id, 53.0, "Meet 3")
    assert repo.average("Swimming") == pytest.approx(53.3333333)
    assert repo.best("Swimming").value == 52.0  # Lab 5 event semantics: smaller time is faster.
    assert repo.maximum("Swimming") == 55.0     # SQL MAX for disciplines where higher scores win.
    assert [r.value for r in repo.ranking("Swimming")] == [52.0, 53.0, 55.0]

def test_batch_transaction_commit(session, seed):
    _, athlete = seed
    rows = [SportsResult("Anna Koval", "Swimming", x, "Junior", datetime(2026, 5, 1)) for x in [52.1, 53.4]]
    saved = save_result_batch(session, rows, {"Anna Koval": athlete.id}, "Regional")
    assert len(saved) == 2 and len(ResultRepository(session).list_all()) == 2

def test_batch_transaction_rolls_back_all_on_invalid_row(session, seed):
    _, athlete = seed
    rows = [SportsResult("Anna Koval", "Swimming", 52.1, "Junior", datetime(2026, 5, 1)), SportsResult("Missing", "Swimming", 51.0, "Junior", datetime(2026, 5, 1))]
    with pytest.raises(ValueError, match="not registered"):
        save_result_batch(session, rows, {"Anna Koval": athlete.id})
    assert ResultRepository(session).list_all() == []


def test_persist_imported_results_creates_related_records(session):
    from sports_streaming.persistence_service import persist_imported_results
    row = SportsResult("Ira Shevchenko", "Running", 12.8, "Senior", datetime(2026, 5, 2))
    persisted = persist_imported_results(session, [row], "Spring Cup")
    result = ResultRepository(session).get(persisted[0].id)
    assert result.athlete.name == "Ira Shevchenko"
    assert result.athlete.sport.name == "Running"
    assert result.competition_date.isoformat() == "2026-05-02"

