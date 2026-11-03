from __future__ import annotations

import asyncio
import os
from typing import Any

import httpx
from fastapi import FastAPI


async def get_json_with_retry(
    client: httpx.AsyncClient, url: str, attempts: int = 3
) -> Any:
    for attempt in range(1, attempts + 1):
        try:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()
        except (httpx.RequestError, httpx.HTTPStatusError):
            if attempt == attempts:
                raise
            await asyncio.sleep(0.1 * attempt)
    raise RuntimeError("Unreachable retry state")


async def fetch_many_rankings(
    app: FastAPI, sport_ids: list[int], concurrency: int = 3
) -> list[dict[str, Any]]:
    semaphore = asyncio.Semaphore(concurrency)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://sports-api.local",
        timeout=httpx.Timeout(5.0),
    ) as client:
        async def fetch_one(sport_id: int) -> dict[str, Any]:
            async with semaphore:
                ranking = await get_json_with_retry(
                    client, f"/sports/{sport_id}/ranking"
                )
                return {"sport_id": sport_id, "ranking": ranking}

        tasks = [asyncio.create_task(fetch_one(sport_id)) for sport_id in sport_ids]
        return await asyncio.gather(*tasks)


async def fetch_external_rankings(
    league_ids: list[int], concurrency: int = 3,
    transport: httpx.AsyncBaseTransport | None = None,
) -> list[dict[str, Any]]:
    api_key = os.getenv("SPORTSDB_API_KEY", "123")
    base_url = f"https://www.thesportsdb.com/api/v1/json/{api_key}"
    semaphore = asyncio.Semaphore(concurrency)
    async with httpx.AsyncClient(
        base_url=base_url,
        timeout=httpx.Timeout(5.0),
        transport=transport,
    ) as client:
        async def fetch_one(league_id: int) -> dict[str, Any]:
            async with semaphore:
                response_data = await get_json_with_retry(
                    client, f"/lookuptable.php?l={league_id}"
                )
                return {"league_id": league_id, "table": response_data.get("table") or []}

        tasks = [asyncio.create_task(fetch_one(league_id)) for league_id in league_ids]
        return await asyncio.gather(*tasks)
