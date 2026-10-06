from datetime import datetime
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from app.models.enums import (
    RecommendationSource,
    RecommendationStatus,
)


class RecommendationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    request_id: UUID

    student_profile_id: UUID
    model_version_id: UUID

    input_snapshot: dict
    input_hash: str | None

    results: dict | list | None
    top_field_id: UUID | None

    status: RecommendationStatus
    latency_ms: int | None
    source: RecommendationSource

    feedback_rating: int | None
    feedback_comment: str | None

    error_code: str | None
    error_message: str | None

    created_at: datetime
    completed_at: datetime | None


class RecommendationFeedbackRequest(BaseModel):
    rating: int = Field(
        ge=1,
        le=5,
    )

    comment: str | None = None
