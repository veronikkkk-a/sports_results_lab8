import asyncio

import httpx
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .database import Base, engine, get_session
from .external_api import fetch_many_external_rankings, fetch_many_sport_rankings
from .schemas import (
    AthleteCreate, AthletePatch, AthleteResponse, RankingEntry, ResultCreate, ResultPatch,
    ResultResponse, SportCreate, SportResponse, SportStatistics,
    SportPatch,
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


@app.get("/sports/{sport_id}", response_model=SportResponse)
async def get_sport(sport_id: int, session: Session = Depends(get_session)):
    try:
        return SportService(session).get(sport_id)
    except ResourceNotFound as exc:
        raise_http_error(exc)


@app.patch("/sports/{sport_id}", response_model=SportResponse)
async def update_sport(
    sport_id: int, data: SportPatch, session: Session = Depends(get_session)
):
    try:
        return SportService(session).update(
            sport_id, data.model_dump(exclude_unset=True)
        )
    except (ResourceNotFound, ResourceConflict) as exc:
        raise_http_error(exc)


@app.delete("/sports/{sport_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sport(sport_id: int, session: Session = Depends(get_session)) -> None:
    try:
        SportService(session).delete(sport_id)
    except ResourceNotFound as exc:
        raise_http_error(exc)


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


@app.get("/athletes/{athlete_id}", response_model=AthleteResponse)
async def get_athlete(athlete_id: int, session: Session = Depends(get_session)):
    try:
        return AthleteService(session).get(athlete_id)
    except ResourceNotFound as exc:
        raise_http_error(exc)


@app.patch("/athletes/{athlete_id}", response_model=AthleteResponse)
async def update_athlete(
    athlete_id: int, data: AthletePatch, session: Session = Depends(get_session)
):
    try:
        return AthleteService(session).update(
            athlete_id, data.model_dump(exclude_unset=True)
        )
    except (ResourceNotFound, ResourceConflict) as exc:
        raise_http_error(exc)


@app.delete("/athletes/{athlete_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_athlete(
    athlete_id: int, session: Session = Depends(get_session)
) -> None:
    try:
        AthleteService(session).delete(athlete_id)
    except ResourceNotFound as exc:
        raise_http_error(exc)


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
        sport, count, average, best, maximum = ResultService(session).statistics(sport_id)
    except ResourceNotFound as exc:
        raise_http_error(exc)
    return SportStatistics(
        sport_id=sport.id,
        sport_name=sport.name,
        results_count=count,
        average_result=float(average) if average is not None else None,
        best_result=float(best) if best is not None else None,
        maximum_result=float(maximum) if maximum is not None else None,
    )


@app.get("/async/rankings")
async def get_async_rankings(sport_ids: list[int] = Query(default=[1, 2])):
    """Паралельно збирає рейтинги кількох видів спорту через HTTPX."""
    if not sport_ids or any(sport_id <= 0 for sport_id in sport_ids):
        raise HTTPException(status_code=422, detail="sport_ids must contain positive IDs")
    if len(sport_ids) > 20:
        raise HTTPException(status_code=422, detail="A maximum of 20 sport IDs is allowed")
    try:
        return await asyncio.wait_for(
            fetch_many_sport_rankings(app, list(dict.fromkeys(sport_ids))),
            timeout=12.0,
        )
    except asyncio.TimeoutError as exc:
        raise HTTPException(status_code=504, detail="Ranking request timed out") from exc
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Sport not found") from exc
        raise HTTPException(status_code=502, detail="Ranking request failed") from exc
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail="Ranking request failed") from exc





@app.get("/async/external-rankings")
async def get_external_rankings(league_ids: list[int] = Query(...)):
    """Паралельно отримує турнірні таблиці ліг із TheSportsDB."""
    if not league_ids or any(league_id <= 0 for league_id in league_ids):
        raise HTTPException(status_code=422, detail="league_ids must contain positive IDs")
    league_ids = list(dict.fromkeys(league_ids))
    if len(league_ids) > 5:
        raise HTTPException(status_code=422, detail="A maximum of 5 league IDs is allowed")
    try:
        return await asyncio.wait_for(
            fetch_many_external_rankings(league_ids), timeout=12.0
        )
    except asyncio.TimeoutError as exc:
        raise HTTPException(status_code=504, detail="External sports API timeout") from exc
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502, detail=f"TheSportsDB returned HTTP {exc.response.status_code}"
        ) from exc
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail="External sports API request failed") from exc
