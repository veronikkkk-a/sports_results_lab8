import pytest


async def create_sport_and_athlete(client):
    sport_response = await client.post(
        "/sports", json={"name": "Swimming", "discipline": "Aquatics"}
    )
    assert sport_response.status_code == 201
    sport = sport_response.json()
    athlete_response = await client.post(
        "/athletes",
        json={"name": "Anna Koval", "category": "Junior", "sport_id": sport["id"]},
    )
    assert athlete_response.status_code == 201
    return sport, athlete_response.json()


@pytest.mark.asyncio
async def test_sport_and_athlete_crud(client):
    sport, athlete = await create_sport_and_athlete(client)
    assert (await client.get(f"/sports/{sport['id']}")).status_code == 200
    filtered = await client.get(
        "/athletes", params={"sport_id": sport["id"], "name": "Anna"}
    )
    assert filtered.json()[0]["id"] == athlete["id"]
    changed_sport = await client.patch(
        f"/sports/{sport['id']}", json={"discipline": "Pool"}
    )
    assert changed_sport.json()["discipline"] == "Pool"
    changed_athlete = await client.patch(
        f"/athletes/{athlete['id']}", json={"category": "Senior"}
    )
    assert changed_athlete.json()["category"] == "Senior"
    assert (await client.delete(f"/athletes/{athlete['id']}")).status_code == 204
    assert (await client.get(f"/athletes/{athlete['id']}")).status_code == 404
    assert (await client.delete(f"/sports/{sport['id']}")).status_code == 204
    assert (await client.get(f"/sports/{sport['id']}")).status_code == 404


@pytest.mark.asyncio
async def test_result_crud_batch_ranking_and_statistics(client):
    sport, athlete = await create_sport_and_athlete(client)
    batch = await client.post(
        "/results/batch",
        json={"results": [
            {"athlete_id": athlete["id"], "value": 52.4, "competition_name": "Cup"},
            {"athlete_id": athlete["id"], "value": 51.9, "competition_name": "Final"},
        ]},
    )
    assert batch.status_code == 201
    result_id = batch.json()[0]["id"]
    assert (await client.get(f"/results/{result_id}")).status_code == 200
    ranking = await client.get(f"/sports/{sport['id']}/ranking")
    assert ranking.json()[0]["value"] == 51.9
    stats = (await client.get(f"/sports/{sport['id']}/statistics")).json()
    assert stats["results_count"] == 2
    assert stats["average_result"] == 52.15
    assert stats["best_result"] == 51.9
    assert stats["maximum_result"] == 52.4
    assert (await client.patch(f"/results/{result_id}", json={"value": None})).status_code == 422
    assert (await client.patch(f"/results/{result_id}", json={"value": 50.5})).status_code == 200
    assert (await client.delete(f"/results/{result_id}")).status_code == 204


@pytest.mark.asyncio
async def test_validation_not_found_conflict_and_atomic_batch(client):
    invalid_sport = await client.post("/sports", json={"name": "S", "discipline": "X"})
    assert invalid_sport.status_code == 422
    sport, athlete = await create_sport_and_athlete(client)
    duplicate = await client.post(
        "/sports", json={"name": "Swimming", "discipline": "Other"}
    )
    assert duplicate.status_code == 409
    no_sport = await client.post(
        "/athletes", json={"name": "No Sport", "category": "AA", "sport_id": 999}
    )
    assert no_sport.status_code == 404
    assert (await client.get("/sports/999/ranking")).status_code == 404
    response = await client.post(
        "/results/batch",
        json={"results": [
            {"athlete_id": athlete["id"], "value": 10, "competition_name": "Valid"},
            {"athlete_id": 999, "value": 11, "competition_name": "Invalid"},
        ]},
    )
    assert response.status_code == 404
    assert (await client.get(f"/sports/{sport['id']}/results")).json() == []


@pytest.mark.asyncio
async def test_async_rankings_for_multiple_sports(client):
    first_sport, first_athlete = await create_sport_and_athlete(client)
    await client.post(
        "/results", json={"athlete_id": first_athlete["id"], "value": 52.4, "competition_name": "Cup"}
    )
    second_sport = (await client.post(
        "/sports", json={"name": "Athletics", "discipline": "Track"}
    )).json()
    second_athlete = (await client.post(
        "/athletes", json={"name": "Oleh Marchenko", "category": "Senior", "sport_id": second_sport["id"]}
    )).json()
    await client.post(
        "/results", json={"athlete_id": second_athlete["id"], "value": 10.8, "competition_name": "Meet"}
    )
    response = await client.get(
        "/async/rankings",
        params=[("sport_ids", first_sport["id"]), ("sport_ids", second_sport["id"])],
    )
    assert response.status_code == 200
    assert [item["sport_id"] for item in response.json()] == [first_sport["id"], second_sport["id"]]
    assert response.json()[0]["ranking"][0]["value"] == 52.4


@pytest.mark.asyncio
async def test_async_rankings_reject_invalid_ids(client):
    assert (await client.get("/async/rankings", params={"sport_ids": 0})).status_code == 422
    assert (await client.get("/async/rankings", params={"sport_ids": 999})).status_code == 404
