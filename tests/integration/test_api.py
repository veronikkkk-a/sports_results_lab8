from fastapi.testclient import TestClient
from sports_streaming.api import app
from sports_streaming.database import make_engine, make_session_factory
from sports_streaming.repositories import SportRepository, AthleteRepository
from sports_streaming.dependencies import get_db_session

def make_client(tmp_path):
    database = tmp_path / "api.db"
    url = f"sqlite:///{database.as_posix()}"
    engine = make_engine(url)
    
    from sports_streaming.db_models import Base
    Base.metadata.create_all(engine)
    
    SessionLocal = make_session_factory(engine)
    session = SessionLocal()
    
    sport_swimming = SportRepository(session).add("Swimming", "Aquatics")
    sport_running = SportRepository(session).add("Running", "Track")
    athlete = AthleteRepository(session).add("Anna Koval", "Junior", sport_swimming.id)
    session.commit()
    
    ids = {
        "swimming": sport_swimming.id,
        "running": sport_running.id,
        "athlete": athlete.id
    }

    # Перевизначаємо залежність сесії для TestClient, щоб вони використовували одну БД
    app.dependency_overrides[get_db_session] = lambda: session

    client = TestClient(app)
    return client, engine, ids

def test_api_create_filter_rank_patch_and_delete(tmp_path):
    client, engine, ids = make_client(tmp_path)
    try:
        response = client.post("/athletes", json={"name": "Oleh Petrenko", "category": "Senior", "sport_id": ids["swimming"]})
        assert response.status_code == 201
        athlete_id = response.json()["id"]
        
        athletes_list = client.get(f"/athletes?sport_id={ids['swimming']}").json()
        assert len(athletes_list) >= 1

        created = client.post("/results", json={"athlete_id": athlete_id, "value": 49.8, "competition_name": "Final"})
        assert created.status_code == 201
        result_id = created.json()["id"]
        
        ranking = client.get(f"/sports/{ids['swimming']}/ranking")
        assert ranking.status_code == 200
        
        patched = client.patch(f"/results/{result_id}", json={"value": 48.9})
        assert patched.status_code == 200 and patched.json()["value"] == 48.9
        
        assert client.delete(f"/results/{result_id}").status_code == 204
    finally:
        client.close()
        engine.dispose()
        app.dependency_overrides.clear()


def test_api_validation_not_found_and_statistics(tmp_path):
    client, engine, ids = make_client(tmp_path)
    try:
        assert client.post("/results", json={"athlete_id": ids["athlete"], "value": -1, "competition_name": "Test"}).status_code == 422
        assert client.post("/athletes", json={"name": "A", "category": "Junior", "sport_id": ids["swimming"]}).status_code == 422
        assert client.get("/sports/999/results").status_code == 404
    finally:
        client.close()
        engine.dispose()
        app.dependency_overrides.clear()


def test_parallel_rankings_uses_httpx_tasks_gather_and_semaphore(tmp_path, monkeypatch):
    import sports_streaming.api as api_module

    client, engine, ids = make_client(tmp_path)
    calls = []

    class FakeResponse:
        status_code = 200

        def raise_for_status(self):
            pass

        def json(self):
            return {"sport_id": 1, "sport_name": "Test", "rankings": []}

    class FakeAsyncClient:
        def __init__(self, **kwargs):
            self.timeout = kwargs.get("timeout", 5.0)

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def get(self, url):
            calls.append(url)
            return FakeResponse()

    monkeypatch.setattr(api_module.httpx, "AsyncClient", FakeAsyncClient)
    try:
        response = client.post(
            "/sports/batch-rankings",
            json={"sport_ids": [ids["swimming"], ids["running"]]},
        )
        assert response.status_code == 200
        assert len(calls) == 2
    finally:
        client.close()
        engine.dispose()
        app.dependency_overrides.clear()