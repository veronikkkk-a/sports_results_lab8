def create_sample(client):
    sport = client.post("/sports", json={"name": "Swimming", "discipline": "Aquatics"})
    assert sport.status_code == 201
    athlete = client.post("/athletes", json={
        "name": "Anna Koval", "category": "Junior", "sport_id": sport.json()["id"]
    })
    assert athlete.status_code == 201
    return sport.json(), athlete.json()

def test_create_and_list_sport_and_athlete(client):
    sport, athlete = create_sample(client)
    assert client.get("/sports").status_code == 200
    response = client.get("/athletes?sport_id=1")
    assert response.status_code == 200
    assert response.json()[0]["name"] == "Anna Koval"

def test_create_patch_delete_result(client):
    _, athlete = create_sample(client)
    created = client.post("/results", json={
        "athlete_id": athlete["id"], "value": 52.4,
        "competition_name": "City Cup", "competition_date": "2026-10-01"
    })
    assert created.status_code == 201
    result_id = created.json()["id"]
    patched = client.patch(f"/results/{result_id}", json={"value": 51.9})
    assert patched.status_code == 200
    assert patched.json()["value"] == 51.9
    deleted = client.delete(f"/results/{result_id}")
    assert deleted.status_code == 204
    assert client.delete(f"/results/{result_id}").status_code == 404

def test_validation_and_not_found(client):
    response = client.post("/results", json={
        "athlete_id": 1, "value": -1, "competition_name": "Cup"
    })
    assert response.status_code == 422
    assert client.get("/sports/999/ranking").status_code == 404

def test_ranking_and_statistics(client):
    sport, athlete = create_sample(client)
    for value in [52.4, 51.9]:
        response = client.post("/results", json={
            "athlete_id": athlete["id"], "value": value, "competition_name": "City Cup"
        })
        assert response.status_code == 201
    ranking = client.get(f"/sports/{sport['id']}/ranking")
    assert ranking.status_code == 200
    assert ranking.json()[0]["value"] == 51.9
    stats = client.get(f"/sports/{sport['id']}/statistics").json()
    assert stats["results_count"] == 2
    assert stats["average_result"] == 52.15
