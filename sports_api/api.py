from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

import httpx
from fastapi import Depends, FastAPI, HTTPException, Query, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .async_client import fetch_external_rankings, fetch_many_rankings
from .database import get_session, initialize_database
from .models import Athlete, Result, Sport
from .schemas import (
    AthleteCreate,
    AthletePatch,
    AthleteResponse,
    RankingEntry,
    ResultBatch,
    ResultCreate,
    ResultPatch,
    ResultResponse,
    SportCreate,
    SportPatch,
    SportResponse,
    SportStatistics,
)
from .services import (
    AthleteService,
    ResourceConflict,
    ResourceNotFound,
    ResultService,
    SportService,
)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    initialize_database()
    yield


app = FastAPI(
    title="Sports Results API",
    version="1.0.0",
    description="REST API for sports, athletes, and competition results (variant 9).",
    lifespan=lifespan,
)


def translate_error(exc: Exception) -> None:
    if isinstance(exc, ResourceNotFound):
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if isinstance(exc, ResourceConflict):
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if isinstance(exc, IntegrityError):
        raise HTTPException(status_code=409, detail="The operation conflicts with stored data") from exc
    raise exc


@app.get("/", tags=["health"])
async def root() -> dict[str, str]:
    return {"message": "Sports Results API is running"}


@app.post("/sports", response_model=SportResponse, status_code=status.HTTP_201_CREATED, tags=["sports"])
async def create_sport(data: SportCreate, session: Session = Depends(get_session)):
    try:
        return SportService(session).create(data.model_dump())
    except (ResourceConflict, IntegrityError) as exc:
        translate_error(exc)


@app.get("/sports", response_model=list[SportResponse], tags=["sports"])
async def list_sports(session: Session = Depends(get_session)):
    return SportService(session).list()


@app.get("/sports/{sport_id}", response_model=SportResponse, tags=["sports"])
async def get_sport(sport_id: int, session: Session = Depends(get_session)):
    try:
        return SportService(session).get(sport_id)
    except ResourceNotFound as exc:
        translate_error(exc)


@app.patch("/sports/{sport_id}", response_model=SportResponse, tags=["sports"])
async def update_sport(sport_id: int, data: SportPatch, session: Session = Depends(get_session)):
    try:
        return SportService(session).update(sport_id, data.model_dump(exclude_unset=True))
    except (ResourceNotFound, ResourceConflict) as exc:
        translate_error(exc)


@app.delete("/sports/{sport_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["sports"])
async def delete_sport(sport_id: int, session: Session = Depends(get_session)) -> Response:
    try:
        SportService(session).delete(sport_id)
    except ResourceNotFound as exc:
        translate_error(exc)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post("/athletes", response_model=AthleteResponse, status_code=status.HTTP_201_CREATED, tags=["athletes"])
async def create_athlete(data: AthleteCreate, session: Session = Depends(get_session)):
    try:
        return AthleteService(session).create(data.model_dump())
    except (ResourceNotFound, ResourceConflict) as exc:
        translate_error(exc)


@app.get("/athletes", response_model=list[AthleteResponse], tags=["athletes"])
async def list_athletes(
    sport_id: int | None = Query(default=None, gt=0),
    name: str | None = Query(default=None, min_length=1, max_length=120),
    session: Session = Depends(get_session),
):
    try:
        return AthleteService(session).list(sport_id, name)
    except ResourceNotFound as exc:
        translate_error(exc)


@app.get("/athletes/{athlete_id}", response_model=AthleteResponse, tags=["athletes"])
async def get_athlete(athlete_id: int, session: Session = Depends(get_session)):
    try:
        return AthleteService(session).get(athlete_id)
    except ResourceNotFound as exc:
        translate_error(exc)


@app.patch("/athletes/{athlete_id}", response_model=AthleteResponse, tags=["athletes"])
async def update_athlete(athlete_id: int, data: AthletePatch, session: Session = Depends(get_session)):
    try:
        return AthleteService(session).update(athlete_id, data.model_dump(exclude_unset=True))
    except (ResourceNotFound, ResourceConflict) as exc:
        translate_error(exc)


@app.delete("/athletes/{athlete_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["athletes"])
async def delete_athlete(athlete_id: int, session: Session = Depends(get_session)) -> Response:
    try:
        AthleteService(session).delete(athlete_id)
    except ResourceNotFound as exc:
        translate_error(exc)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post("/results", response_model=ResultResponse, status_code=status.HTTP_201_CREATED, tags=["results"])
async def create_result(data: ResultCreate, session: Session = Depends(get_session)):
    try:
        return ResultService(session).create(data.model_dump())
    except ResourceNotFound as exc:
        translate_error(exc)
    except IntegrityError as exc:
        translate_error(exc)


@app.post("/results/batch", response_model=list[ResultResponse], status_code=status.HTTP_201_CREATED, tags=["results"])
async def create_result_batch(data: ResultBatch, session: Session = Depends(get_session)):
    try:
        items = [item.model_dump() for item in data.results]
        return ResultService(session).create_batch(items)
    except ResourceNotFound as exc:
        translate_error(exc)
    except IntegrityError as exc:
        translate_error(exc)


@app.get("/results/{result_id}", response_model=ResultResponse, tags=["results"])
async def get_result(result_id: int, session: Session = Depends(get_session)):
    try:
        return ResultService(session).get(result_id)
    except ResourceNotFound as exc:
        translate_error(exc)


@app.patch("/results/{result_id}", response_model=ResultResponse, tags=["results"])
async def update_result(result_id: int, data: ResultPatch, session: Session = Depends(get_session)):
    try:
        return ResultService(session).update(result_id, data.model_dump(exclude_unset=True))
    except ResourceNotFound as exc:
        translate_error(exc)
    except IntegrityError as exc:
        translate_error(exc)


@app.delete("/results/{result_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["results"])
async def delete_result(result_id: int, session: Session = Depends(get_session)) -> Response:
    try:
        ResultService(session).delete(result_id)
    except ResourceNotFound as exc:
        translate_error(exc)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/sports/{sport_id}/results", response_model=list[ResultResponse], tags=["results"])
async def list_sport_results(sport_id: int, session: Session = Depends(get_session)):
    try:
        return ResultService(session).list_for_sport(sport_id)
    except ResourceNotFound as exc:
        translate_error(exc)


@app.get("/sports/{sport_id}/ranking", response_model=list[RankingEntry], tags=["statistics"])
async def get_ranking(sport_id: int, session: Session = Depends(get_session)):
    try:
        rows = ResultService(session).ranking(sport_id)
    except ResourceNotFound as exc:
        translate_error(exc)
    return [
        RankingEntry(
            athlete_id=result.athlete.id,
            athlete_name=result.athlete.name,
            category=result.athlete.category,
            value=result.value,
            competition_name=result.competition_name,
            competition_date=result.competition_date,
        )
        for result in rows
    ]


@app.get("/sports/{sport_id}/statistics", response_model=SportStatistics, tags=["statistics"])
async def get_statistics(sport_id: int, session: Session = Depends(get_session)):
    try:
        sport, count, average, best, maximum = ResultService(session).statistics(sport_id)
    except ResourceNotFound as exc:
        translate_error(exc)
    return SportStatistics(
        sport_id=sport.id,
        sport_name=sport.name,
        results_count=count,
        average_result=average,
        best_result=best,
        maximum_result=maximum,
    )


@app.get("/async/rankings", tags=["async"])
async def get_async_rankings(sport_ids: list[int] = Query(default=[1, 2])):
    if not sport_ids or any(item <= 0 for item in sport_ids):
        raise HTTPException(status_code=422, detail="sport_ids must contain positive IDs")
    if len(sport_ids) > 20:
        raise HTTPException(status_code=422, detail="At most 20 sport IDs are allowed")
    unique_ids = list(dict.fromkeys(sport_ids))
    try:
        return await asyncio.wait_for(fetch_many_rankings(app, unique_ids), timeout=12.0)
    except asyncio.TimeoutError as exc:
        raise HTTPException(status_code=504, detail="Ranking request timed out") from exc
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Sport not found") from exc
        raise HTTPException(status_code=502, detail="Ranking request failed") from exc
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail="Ranking request failed") from exc


@app.get("/async/external-rankings", tags=["async"])
async def get_external_rankings(league_ids: list[int] = Query(...)):
    if not league_ids or any(item <= 0 for item in league_ids):
        raise HTTPException(status_code=422, detail="league_ids must contain positive IDs")
    unique_ids = list(dict.fromkeys(league_ids))
    if len(unique_ids) > 5:
        raise HTTPException(status_code=422, detail="At most 5 league IDs are allowed")
    try:
        return await asyncio.wait_for(fetch_external_rankings(unique_ids), timeout=12.0)
    except asyncio.TimeoutError as exc:
        raise HTTPException(status_code=504, detail="External sports API timed out") from exc
    except (httpx.HTTPStatusError, httpx.RequestError) as exc:
        raise HTTPException(status_code=502, detail="External sports API request failed") from exc
