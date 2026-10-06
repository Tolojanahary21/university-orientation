from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class StudentProfileCreate(BaseModel):
    bac_series: str = Field(
        min_length=1,
        max_length=50,
    )

    graduation_year: int | None = None

    scores: dict[str, float] | None = None

    average_score: Decimal | None = None

    mention: str | None = Field(
        default=None,
        max_length=50,
    )

    preferences: dict | None = None


class StudentProfileUpdate(BaseModel):
    bac_series: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
    )

    graduation_year: int | None = None

    scores: dict[str, float] | None = None

    average_score: Decimal | None = None

    mention: str | None = Field(
        default=None,
        max_length=50,
    )

    preferences: dict | None = None


class StudentProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID

    bac_series: str
    graduation_year: int | None

    scores: dict[str, float] | None
    average_score: Decimal | None
    mention: str | None
    preferences: dict | None

    profile_version: int

    created_at: datetime
    updated_at: datetime
