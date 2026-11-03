from datetime import date
from pydantic import BaseModel, Field, ConfigDict

class SportCreate(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    discipline: str = Field(min_length=2, max_length=80)

class SportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    discipline: str

class AthleteCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    category: str = Field(min_length=2, max_length=80)
    sport_id: int = Field(gt=0)

class AthleteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    category: str
    sport_id: int

class ResultCreate(BaseModel):
    athlete_id: int = Field(gt=0)
    value: float = Field(ge=0)
    competition_name: str = Field(min_length=2, max_length=120)
    competition_date: date | None = None

class ResultPatch(BaseModel):
    athlete_id: int | None = Field(default=None, gt=0)
    value: float | None = Field(default=None, ge=0)
    competition_name: str | None = Field(default=None, min_length=2, max_length=120)
    competition_date: date | None = None

class ResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    athlete_id: int
    value: float
    competition_name: str
    competition_date: date | None

class RankingEntry(BaseModel):
    athlete_id: int
    athlete_name: str
    category: str
    value: float
    competition_name: str
    competition_date: date | None

class SportStatistics(BaseModel):
    sport_id: int
    sport_name: str
    results_count: int
    average_result: float | None
    best_result: float | None
