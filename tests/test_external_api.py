import httpx
import pytest

from sports_api.async_client import fetch_external_rankings


@pytest.mark.asyncio
async def test_external_rankings_retry_and_gather():
    calls = {}

    def handler(request: httpx.Request):
        league_id = int(request.url.params["l"])
        calls[league_id] = calls.get(league_id, 0) + 1
        if league_id == 4328 and calls[league_id] == 1:
            return httpx.Response(503, json={"message": "temporary"})
        return httpx.Response(200, json={"table": [{"rank": 1, "name": f"League {league_id}"}]})

    results = await fetch_external_rankings(
        [4328, 4331], concurrency=2, transport=httpx.MockTransport(handler)
    )
    assert calls == {4328: 2, 4331: 1}
    assert [row["league_id"] for row in results] == [4328, 4331]
