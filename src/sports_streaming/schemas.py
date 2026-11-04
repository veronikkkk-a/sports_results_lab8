from datetime import date
from pydantic import BaseModel, Field, ConfigDict

# --- Sport Schemas ---
class SportBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=80)
    discipline: str = Field(..., min_length=2, max_length=80)

class SportCreate(SportBase):
    pass

class SportResponse(SportBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# --- Athlete Schemas ---
class AthleteBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    category: str = Field(..., min_length=2, max_length=80)
    sport_id: int = Field(..., gt=0)

class AthleteCreate(AthleteBase):
    pass

class AthleteResponse(AthleteBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# --- Result Schemas ---
class ResultCreate(BaseModel):
    athlete_id: int = Field(..., gt=0)
    value: float = Field(..., ge=0.0, description="Значення результату не може бути від'ємним")
    competition_name: str = Field(..., min_length=2, max_length=120)
    competition_date: date | None = None

class ResultUpdate(BaseModel):
    value: float | None = Field(default=None, ge=0.0)
    competition_name: str | None = Field(default=None, min_length=2, max_length=120)
    competition_date: date | None = None

class ResultResponse(BaseModel):
    id: int
    athlete_id: int
    value: float
    competition_name: str
    competition_date: date | None = None
    model_config = ConfigDict(from_attributes=True)

# --- Ranking / Aggregation Schemas ---
class AthleteRankingItem(BaseModel):
    athlete_id: int
    athlete_name: str
    category: str
    best_value: float

class SportRankingResponse(BaseModel):
    sport_id: int
    sport_name: str
    rankings: list[AthleteRankingItem]

class BatchRankingRequest(BaseModel):
    sport_ids: list[int] = Field(..., min_length=1)
