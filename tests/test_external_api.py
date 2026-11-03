import httpx
import pytest

from sports_api.external_api import fetch_many_external_rankings


@pytest.mark.asyncio
async def test_external_rankings_use_httpx_and_retry():
    calls: dict[int, int] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        league_id = int(request.url.params["l"])
        calls[league_id] = calls.get(league_id, 0) + 1
        if league_id == 4328 and calls[league_id] == 1:
            return httpx.Response(503, json={"message": "temporary error"})
        return httpx.Response(
            200,
            json={"table": [{"name": f"Team {league_id}", "rank": 1}]},
        )

    results = await fetch_many_external_rankings(
        [4328, 4331],
        concurrency=2,
        transport=httpx.MockTransport(handler),
    )

    assert calls == {4328: 2, 4331: 1}
    assert results == [
        {"league_id": 4328, "table": [{"name": "Team 4328", "rank": 1}]},
        {"league_id": 4331, "table": [{"name": "Team 4331", "rank": 1}]},
    ]
