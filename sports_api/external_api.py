import asyncio
import httpx

async def get_json_with_retry(
    client: httpx.AsyncClient,
    url: str,
    attempts: int = 3,
) -> dict:
    """HTTPX request із timeout та повторними спробами."""
    for attempt in range(1, attempts + 1):
        try:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()
        except (httpx.RequestError, httpx.HTTPStatusError):
            if attempt == attempts:
                raise
            await asyncio.sleep(attempt)
    raise RuntimeError("Request failed")

async def fetch_public_posts(post_id: int = 1) -> dict:
    """Демонстраційний запит до відкритого тестового API."""
    timeout = httpx.Timeout(5.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        return await get_json_with_retry(
            client,
            f"https://jsonplaceholder.typicode.com/posts/{post_id}",
        )

async def fetch_many_public_posts(post_ids: list[int]) -> list[dict]:
    """Паралельні HTTP-запити з Task, gather та обмеженням Semaphore."""
    semaphore = asyncio.Semaphore(3)
    timeout = httpx.Timeout(5.0)

    async with httpx.AsyncClient(timeout=timeout) as client:
        async def limited_fetch(post_id: int) -> dict:
            async with semaphore:
                return await get_json_with_retry(
                    client,
                    f"https://jsonplaceholder.typicode.com/posts/{post_id}",
                )

        tasks = [
            asyncio.create_task(limited_fetch(post_id))
            for post_id in post_ids
        ]
        return await asyncio.gather(*tasks)

async def demo_timeout() -> str:
    async def slow_operation() -> str:
        await asyncio.sleep(2)
        return "finished"

    try:
        return await asyncio.wait_for(slow_operation(), timeout=0.5)
    except asyncio.TimeoutError:
        return "Operation timed out"
