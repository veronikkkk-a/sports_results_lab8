# Лабораторна робота №7 — база даних спортивних результатів

Варіант 9 продовжує пакет `sports_streaming` із попередніх робіт: CSV-валідація та потокова обробка збережені, а persistence layer записує результати у SQLite. Він побудований на SQLAlchemy ORM і Repository Pattern; окремий DB-API запит показує параметризований пошук за видом спорту.

## Встановлення та запуск (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[test]"
python -m alembic upgrade head
python -m sports_streaming.main --persist-db
python -m uvicorn sports_streaming.api:app --reload
```

## REST API (ЛР 8)

FastAPI працює з тими самими таблицями SQLite і Repository Layer, що й імпорт CSV.
Документація OpenAPI доступна на `http://127.0.0.1:8000/docs`.

Основні маршрути:

| Метод | Маршрут | Призначення |
|---|---|---|
| GET | `/athletes?sport_id=1&name=Anna` | Список і фільтрація спортсменів |
| POST | `/athletes` | Створення спортсмена |
| GET | `/results?sport_id=1` | Перелік результатів |
| POST | `/results` | Додавання результату |
| PATCH / DELETE | `/results/{result_id}` | Зміна / видалення результату |
| GET | `/sports/{sport_id}/results` | Результати виду спорту |
| GET | `/sports/{sport_id}/ranking?limit=10` | Рейтинг (менше значення — вище місце) |
| GET | `/sports/{sport_id}/statistics` | Кількість, середнє та найкраще значення |
| GET | `/rankings/parallel?sport_ids=1&sport_ids=2` | HTTPX запити до кількох рейтингів паралельно |

Асинхронний агрегатор використовує `asyncio.Task`, `gather`, `Semaphore`, timeout та retry.
Налаштовуються `base_url`, `timeout_seconds`, `retries` і `concurrency`. Для локального запуску:

```powershell
python -m uvicorn sports_streaming.api:app --reload
```

Без прапорця `--persist-db` попередній режим CSV → JSON продовжує працювати. Типовий файл бази `sports_results.db` створюється в корені проєкту. Можна передати інший шлях:

```powershell
python -m sports_streaming.main --persist-db --database-url "sqlite:///my_results.db"
```

## Тести

```powershell
python -m pytest -v
```

Тести запускаються на окремій SQLite in-memory базі; вони не торкаються production БД. Є перевірки CRUD для всіх трьох сутностей, зв'язків, обмежень, DB-API-фільтра, AVG/MAX-рейтингів, commit/rollback та Alembic migrations.

## Структура

```text
src/sports_streaming/  # ЛР5/ЛР6-пакет і persistence layer
migrations/             # початкова схема та migration з датою змагання
tests/integration/      # інтеграційні перевірки на тестовій SQLite
report/                 # звіт та докази запуску
```
