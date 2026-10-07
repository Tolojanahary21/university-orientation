from pydantic import BaseModel, ConfigDict, Field, field_validator


class Score(BaseModel):
    raw_subject: str
    raw_score: float
    max_score: float
    normalized_score: float = Field(ge=0, le=20)
    coefficient: float | None = Field(default=None, ge=0)
    optional: bool = False
    confidence: float = Field(ge=0, le=1, default=1)
    warning: str | None = None

    @field_validator("raw_score", "max_score")
    @classmethod
    def finite_observation(cls, value):
        if not __import__("math").isfinite(value):
            raise ValueError("score must be finite")
        return value


class ExtractedRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")
    record_id: str
    source_sha256: str
    extraction_version: str
    bac_series: str | None = None
    graduation_year: int | None = None
    scores: dict[str, Score]
    average_score: float | None = Field(default=None, ge=0, le=20)
    mention: str | None = None
    warnings: list[str] = []
    validated: bool = False
    target_field_code: str | None = None


class ValidatedRecord(ExtractedRecord):
    validated: bool
    validated_at: str
    target_field_code: str

    @field_validator("target_field_code")
    @classmethod
    def nonempty_target(cls, value):
        if not value.strip():
            raise ValueError("target_field_code is required")
        return value.strip()


class TrainingRecord(BaseModel):
    record_id: str
    target_field_code: str
    scores: dict[str, float]


class PredictionInput(BaseModel):
    bac_series: str | None = None
    graduation_year: int | None = None
    scores: dict[str, float]
    average_score: float | None = Field(default=None, ge=0, le=20)
    mention: str | None = None


class PredictionResult(BaseModel):
    field_code: str
    probability: float
    rank: int


def __getattr__(name):
    if name in {"InvalidTrainingRecord", "UnknownFieldCode"}:
        return type(name, (ValueError,), {})
    raise AttributeError(name)

