import asyncio
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .database import Base, engine, get_session
from .external_api import fetch_many_public_posts
from .schemas import (
    AthleteCreate, AthleteResponse, RankingEntry, ResultCreate, ResultPatch,
    ResultResponse, SportCreate, SportResponse, SportStatistics,
)
from .services import AthleteService, ResourceConflict, ResourceNotFound, ResultService, SportService


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Sports Results API",
    version="1.0.0",
    description="REST API для обліку спортивних результатів (варіант 9)",
    lifespan=lifespan,
)


def raise_http_error(exc: Exception) -> None:
    if isinstance(exc, ResourceNotFound):
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if isinstance(exc, ResourceConflict):
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    raise exc


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Sports Results API is running"}


@app.post("/sports", response_model=SportResponse, status_code=status.HTTP_201_CREATED)
async def create_sport(data: SportCreate, session: Session = Depends(get_session)):
    try:
        return SportService(session).create(data.name, data.discipline)
    except (ResourceConflict, ResourceNotFound) as exc:
        raise_http_error(exc)


@app.get("/sports", response_model=list[SportResponse])
async def get_sports(session: Session = Depends(get_session)):
    return SportService(session).list()


@app.post("/athletes", response_model=AthleteResponse, status_code=status.HTTP_201_CREATED)
async def create_athlete(data: AthleteCreate, session: Session = Depends(get_session)):
    try:
        return AthleteService(session).create(data.name, data.category, data.sport_id)
    except (ResourceConflict, ResourceNotFound) as exc:
        raise_http_error(exc)


@app.get("/athletes", response_model=list[AthleteResponse])
async def get_athletes(
    sport_id: int | None = Query(default=None, gt=0),
    name: str | None = Query(default=None, min_length=1),
    session: Session = Depends(get_session),
):
    return AthleteService(session).list(sport_id, name)


@app.post("/results", response_model=ResultResponse, status_code=status.HTTP_201_CREATED)
async def create_result(data: ResultCreate, session: Session = Depends(get_session)):
    try:
        return ResultService(session).create(data.model_dump())
    except ResourceNotFound as exc:
        raise_http_error(exc)


@app.patch("/results/{result_id}", response_model=ResultResponse)
async def update_result(
    result_id: int, data: ResultPatch, session: Session = Depends(get_session)
):
    try:
        return ResultService(session).update(result_id, data.model_dump(exclude_unset=True))
    except ResourceNotFound as exc:
        raise_http_error(exc)


@app.delete("/results/{result_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_result(result_id: int, session: Session = Depends(get_session)) -> None:
    try:
        ResultService(session).delete(result_id)
    except ResourceNotFound as exc:
        raise_http_error(exc)


@app.get("/sports/{sport_id}/results", response_model=list[ResultResponse])
async def get_sport_results(sport_id: int, session: Session = Depends(get_session)):
    try:
        return ResultService(session).list_for_sport(sport_id)
    except ResourceNotFound as exc:
        raise_http_error(exc)


@app.get("/sports/{sport_id}/ranking", response_model=list[RankingEntry])
async def get_sport_ranking(sport_id: int, session: Session = Depends(get_session)):
    try:
        rows = ResultService(session).ranking(sport_id)
    except ResourceNotFound as exc:
        raise_http_error(exc)
    return [
        RankingEntry(
            athlete_id=athlete.id,
            athlete_name=athlete.name,
            category=athlete.category,
            value=result.value,
            competition_name=result.competition_name,
            competition_date=result.competition_date,
        )
        for result, athlete in rows
    ]


@app.get("/sports/{sport_id}/statistics", response_model=SportStatistics)
async def get_sport_statistics(sport_id: int, session: Session = Depends(get_session)):
    try:
        sport, count, average, best = ResultService(session).statistics(sport_id)
    except ResourceNotFound as exc:
        raise_http_error(exc)
    return SportStatistics(
        sport_id=sport.id,
        sport_name=sport.name,
        results_count=count,
        average_result=float(average) if average is not None else None,
        best_result=float(best) if best is not None else None,
    )


@app.get("/async/public-posts")
async def get_public_posts(ids: list[int] = Query(default=[1, 2, 3], ge=1, le=100)):
    """Демонстрація Task/gather/Semaphore/HTTPX; потребує доступу до Інтернету."""
    try:
        return await asyncio.wait_for(fetch_many_public_posts(ids), timeout=12.0)
    except asyncio.TimeoutError as exc:
        raise HTTPException(status_code=504, detail="External API timeout") from exc
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"External API request failed: {type(exc).__name__}",
        ) from exc
