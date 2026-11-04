import pytest
from httpx import AsyncClient, ASGITransport
from sports_streaming.api import app
from sports_streaming.dependencies import get_db_session

@pytest.mark.asyncio
async def test_get_athletes_empty(db_session):
    app.dependency_overrides[get_db_session] = lambda: db_session
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get("/athletes")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    finally:
        app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_create_athlete_validation_error():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/athletes", json={"name": "A", "category": "Junior", "sport_id": -1})
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_full_result_lifecycle(db_session):
    app.dependency_overrides[get_db_session] = lambda: db_session
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            from sports_streaming.repositories import SportRepository, AthleteRepository
            sport = SportRepository(db_session).add("Swimming", "Aquatics")
            athlete = AthleteRepository(db_session).add("Test Athlete", "Junior", sport.id)
            db_session.commit()

            # 1. Створення результату з реальним athlete_id
            res_post = await ac.post("/results", json={
                "athlete_id": athlete.id,
                "value": 10.5,
                "competition_name": "Open Championship"
            })
            assert res_post.status_code == 201
            res_id = res_post.json()["id"]

            # 2. PATCH оновлення
            res_patch = await ac.patch(f"/results/{res_id}", json={"value": 10.2})
            assert res_patch.status_code == 200
            assert res_patch.json()["value"] == 10.2

            # 3. DELETE видалення
            res_del = await ac.delete(f"/results/{res_id}")
            assert res_del.status_code == 204
    finally:
        app.dependency_overrides.clear()