import httpx
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session

from sports_streaming.dependencies import get_db_session
from sports_streaming.repositories import SportRepository, AthleteRepository, ResultRepository
from sports_streaming.schemas import (
    AthleteCreate, AthleteResponse,
    ResultCreate, ResultUpdate, ResultResponse,
    SportRankingResponse, AthleteRankingItem,
    BatchRankingRequest
)
from sports_streaming.external_api import fetch_batch_rankings_concurrently

app = FastAPI(
    title="Sports Results Management REST API",
    version="1.0.0",
    description="REST API для обліку спортивних результатів та паралельної асинхронної обробки рейтингів."
)

@app.get("/athletes", response_model=list[AthleteResponse])
async def get_athletes(
    sport_id: int | None = None,
    session: Session = Depends(get_db_session)
):
    repo = AthleteRepository(session)
    # Метод list_all у вашому AthleteRepository приймає sport_id як аргумент
    return repo.list_all(sport_id=sport_id)

@app.post("/athletes", response_model=AthleteResponse, status_code=status.HTTP_201_CREATED)
async def create_athlete(
    data: AthleteCreate,
    session: Session = Depends(get_db_session)
):
    sport_repo = SportRepository(session)
    # Використовуємо .get() замість .get_by_id()
    if not sport_repo.get(data.sport_id):
        raise HTTPException(status_code=404, detail="Sport not found")
        
    athlete_repo = AthleteRepository(session)
    athlete = athlete_repo.add(name=data.name, category=data.category, sport_id=data.sport_id)
    return athlete

@app.post("/results", response_model=ResultResponse, status_code=status.HTTP_201_CREATED)
async def create_result(
    data: ResultCreate,
    session: Session = Depends(get_db_session)
):
    athlete_repo = AthleteRepository(session)
    if not athlete_repo.get(data.athlete_id):
        raise HTTPException(status_code=404, detail="Athlete not found")
        
    result_repo = ResultRepository(session)
    result = result_repo.add(
        athlete_id=data.athlete_id,
        value=data.value,
        competition_name=data.competition_name,
        competition_date=data.competition_date
    )
    return result

@app.patch("/results/{result_id}", response_model=ResultResponse)
async def update_result(
    result_id: int,
    data: ResultUpdate,
    session: Session = Depends(get_db_session)
):
    repo = ResultRepository(session)
    result = repo.get(result_id)
    if not result:
        raise HTTPException(status_code=404, detail="Result record not found")
    
    updated = repo.update(
        result_id,
        value=data.value,
        competition_name=data.competition_name
    )
    return updated

@app.delete("/results/{result_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_result(
    result_id: int,
    session: Session = Depends(get_db_session)
):
    repo = ResultRepository(session)
    success = repo.delete(result_id)
    if not success:
        raise HTTPException(status_code=404, detail="Result record not found")

@app.get("/sports/{sport_id}/results", response_model=list[ResultResponse])
async def get_sport_results(
    sport_id: int,
    session: Session = Depends(get_db_session)
):
    sport_repo = SportRepository(session)
    sport = sport_repo.get(sport_id)
    if not sport:
        raise HTTPException(status_code=404, detail="Sport not found")
    
    result_repo = ResultRepository(session)
    # Фільтруємо результати за назвою спорту через метод репозиторію list_all(sport=...)
    return result_repo.list_all(sport=sport.name)

@app.get("/sports/{sport_id}/ranking", response_model=SportRankingResponse)
async def get_sport_ranking(
    sport_id: int,
    session: Session = Depends(get_db_session)
):
    sport_repo = SportRepository(session)
    sport = sport_repo.get(sport_id)
    if not sport:
        raise HTTPException(status_code=404, detail="Sport not found")
        
    result_repo = ResultRepository(session)
    raw_ranking = result_repo.ranking(sport.name)
    
    rankings_items = [
        AthleteRankingItem(
            athlete_id=item.athlete.id,
            athlete_name=item.athlete.name,
            category=item.athlete.category,
            best_value=item.value
        ) for item in raw_ranking
    ]
    return SportRankingResponse(sport_id=sport.id, sport_name=sport.name, rankings=rankings_items)

@app.post("/sports/batch-rankings", response_model=list[SportRankingResponse])
async def get_batch_rankings(
    request_data: BatchRankingRequest
):
    try:
        rankings = await fetch_batch_rankings_concurrently(
            base_url="http://127.0.0.1:8000",
            sport_ids=request_data.sport_ids
        )
        return rankings
    except TimeoutError:
        raise HTTPException(status_code=504, detail="Batch aggregation request timed out")