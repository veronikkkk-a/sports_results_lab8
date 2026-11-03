import asyncio
from typing import Any

import httpx
from fastapi import FastAPI


async def get_json_with_retry(
    client: httpx.AsyncClient,
    url: str,
    attempts: int = 3,
) -> Any:
    """Виконує HTTP GET із timeout та повторними спробами."""
    for attempt in range(1, attempts + 1):
        try:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()
        except (httpx.RequestError, httpx.HTTPStatusError):
            if attempt == attempts:
                raise
            await asyncio.sleep(attempt * 0.1)
    raise RuntimeError("Request failed")


async def fetch_many_sport_rankings(
    app: FastAPI,
    sport_ids: list[int],
    concurrency: int = 3,
) -> list[dict[str, Any]]:
    """Паралельно отримує рейтинги через HTTP API з обмеженням паралельності."""
    semaphore = asyncio.Semaphore(concurrency)
    timeout = httpx.Timeout(5.0)
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://sports-api.local",
        timeout=timeout,
    ) as client:
        async def fetch_one(sport_id: int) -> dict[str, Any]:
            async with semaphore:
                ranking = await get_json_with_retry(
                    client,
                    f"/sports/{sport_id}/ranking",
                )
                return {"sport_id": sport_id, "ranking": ranking}

        tasks = [asyncio.create_task(fetch_one(sport_id)) for sport_id in sport_ids]
        return await asyncio.gather(*tasks)
