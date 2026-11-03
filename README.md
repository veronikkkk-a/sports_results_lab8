# Lab 08 — Sports Results API

Variant 9. FastAPI REST service for sports, athletes, and competition results. The code is self-contained and follows the same model, repository, service, and database boundaries used in Lab 7.

## Install and run (Windows PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[test]"
python -m uvicorn sports_api.api:app --reload
```

Open Swagger UI at `http://127.0.0.1:8000/docs`.

Run tests in a second terminal:

```powershell
python -m pytest -v
```

The service creates `sports_results.db` in the working directory on first launch. To reuse the database created by Lab 7, set `SPORTS_DB_URL` before starting the API:

```powershell
$env:SPORTS_DB_URL = "sqlite:///C:/Users/Veronika/Phyton/lab7/sports_results.db"
python -m uvicorn sports_api.api:app --reload
```

## REST API

| Method | Path | Action |
| --- | --- | --- |
| GET, POST | `/sports` | List or create sports |
| GET, PATCH, DELETE | `/sports/{sport_id}` | Read, update, or delete one sport |
| GET, POST | `/athletes` | Filter or create athletes |
| GET, PATCH, DELETE | `/athletes/{athlete_id}` | Read, update, or delete one athlete |
| POST | `/results` | Create one result |
| POST | `/results/batch` | Atomically create a batch of results |
| GET, PATCH, DELETE | `/results/{result_id}` | Read, update, or delete one result |
| GET | `/sports/{sport_id}/results` | List results for a sport |
| GET | `/sports/{sport_id}/ranking` | List results in ascending order (lower time is better) |
| GET | `/sports/{sport_id}/statistics` | Count, average, minimum, and maximum |
| GET | `/async/rankings?sport_ids=1&sport_ids=2` | Fetch several local rankings concurrently |
| GET | `/async/external-rankings?league_ids=4328&league_ids=4331` | Fetch external league tables concurrently |

The asynchronous endpoints demonstrate HTTPX `AsyncClient`, coroutines, `asyncio.Task`, `gather`, `Semaphore`, a request timeout, and retries. The external endpoint uses TheSportsDB's public JSON API; configure `SPORTSDB_API_KEY` to use a different key.
