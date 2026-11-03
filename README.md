# Лабораторна робота №8 — REST API спортивних результатів

Варіант 9. API для видів спорту, спортсменів і результатів. Проєкт використовує FastAPI,
Pydantic, SQLAlchemy, SQLite, HTTPX, asyncio Task/gather, timeout, retry та Semaphore.

## Windows PowerShell (VS Code)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[test]"
python -m uvicorn sports_api.api:app --reload
```

Swagger UI: http://127.0.0.1:8000/docs

В іншому терміналі:
```powershell
python -m pytest -v
```

Це самодостатній навчальний варіант, який створює `sports_results.db` у поточній папці.
Щоб під'єднати саме БД лабораторної №7, встановіть змінну середовища `SPORTS_DB_URL`
на шлях до її SQLite-файлу перед запуском, наприклад:
```powershell
$env:SPORTS_DB_URL = "sqlite:///C:/шлях/до/sports_results.db"
```
Схема таблиць відповідає `sports`, `athletes`, `results` з Lab 07; якщо у вашому проєкті
назви полів або типи відрізняються, узгодьте їх із `models.py` перед підключенням.


Асинхронні рейтинги кількох видів спорту: GET /async/rankings?sport_ids=1&sport_ids=2.

Зовнішні таблиці ліг можна отримати паралельно через `GET /async/external-rankings?league_ids=4328&league_ids=4331`.
Це числові ID ліг TheSportsDB. За потреби задайте ключ змінною `SPORTSDB_API_KEY`; для безкоштовного API використовується ключ `123`.
Локальні рейтинги з бази проєкту доступні через `/async/rankings?sport_ids=1&sport_ids=2`.
