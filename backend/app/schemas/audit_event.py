from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AuditEventCreate(BaseModel):
    trace_id: UUID | None = None
    actor_user_id: UUID | None = None

    event_type: str

    entity_type: str | None = None
    entity_id: UUID | None = None

    action: str | None = None

    old_values: dict | None = None
    new_values: dict | None = None

    metadata: dict | None = None


class AuditEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    trace_id: UUID | None
    actor_user_id: UUID | None

    event_type: str

    entity_type: str | None
    entity_id: UUID | None

    action: str | None

    old_values: dict | None
    new_values: dict | None

    metadata: dict | None = Field(
        default=None,
        validation_alias="event_metadata",
        serialization_alias="metadata",
    )

    created_at: datetime
