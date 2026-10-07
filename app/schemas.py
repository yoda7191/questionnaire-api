from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field, StrictInt, field_validator

class ScaleSummary(BaseModel):
    id: str
    name: str
    item_count: int
    subscales: list[str]

class ItemPublic(BaseModel):
    id: str
    text: str

class ScalePublic(BaseModel):
    id: str
    name: str
    description: str
    source: str
    instructions: str
    response_min: int
    response_max: int
    response_labels: dict[str, str]
    items: list[ItemPublic]

class SubmissionCreate(BaseModel):
    answers: dict[str, StrictInt] = Field(min_length=1)

    model_config = ConfigDict(
        json_schema_extra={"examples": [{"answers": {"e1": 4, "e2": 2, "a1": 5, "a2": 1}}]}
    )

class SubmissionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    scale_id: str
    scores: dict[str, float]
    created_at: datetime

    @field_validator("created_at")
    @classmethod
    def ensure_utc(cls, value: datetime) -> datetime:
        return value if value.tzinfo else value.replace(tzinfo=UTC)

class SubmissionDetail(SubmissionRead):
    answers: dict[str, int]

class SubscaleStats(BaseModel):
    mean: float | None
    sd: float | None

class ScaleStats(BaseModel):
    scale_id: str
    n: int
    subscales: dict[str, SubscaleStats]

class AnswerError(BaseModel):
    item: str  
    error: str

class AnswerErrorResponse(BaseModel):
    detail: list[AnswerError]

class Health(BaseModel):
    status: str