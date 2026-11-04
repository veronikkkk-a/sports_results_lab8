import asyncio
import httpx
from typing import Any

# Обмеження кількості паралельних запитів за допомогою Semaphore (макс 3 одночасно)
MAX_CONCURRENT_REQUESTS = 3
semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

async def fetch_ranking_with_retry(
    client: httpx.AsyncClient,
    url: str,
    max_retries: int = 3
) -> dict[str, Any]:
    """Виконує HTTP GET запит з обмеженням семафора та логікою retry."""
    async with semaphore:
        for attempt in range(1, max_retries + 1):
            try:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()
            except (httpx.RequestError, httpx.HTTPStatusError) as exc:
                if attempt == max_retries:
                    raise exc
                # Exponential backoff
                await asyncio.sleep(0.2 * (2 ** (attempt - 1)))
        raise RuntimeError("Unexpected end of retry loop")

async def fetch_batch_rankings_concurrently(
    base_url: str,
    sport_ids: list[int]
) -> list[dict[str, Any]]:
    """Паралельно отримує рейтинги кількох видів спорту через Tasks, gather та timeout."""
    async with httpx.AsyncClient(timeout=5.0) as client:
        tasks = []
        for sport_id in sport_ids:
            url = f"{base_url}/sports/{sport_id}/ranking"
            # Створення asyncio.Task для кожного запиту
            task = asyncio.create_task(
                fetch_ranking_with_retry(client, url)
            )
            tasks.append(task)

        try:
            # Обгортка asyncio.gather у wait_for для дотримання timeout
            results = await asyncio.wait_for(
                asyncio.gather(*tasks),
                timeout=8.0
            )
            return list(results)
        except asyncio.TimeoutError:
            # Скасовуємо задачі при перевищенні лиміту часу
            for t in tasks:
                t.cancel()
            raise TimeoutError("Concurrently fetching rankings timed out")