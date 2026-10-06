from uuid import UUID

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.core.audit_sanitizer import sanitize_audit_value
from app.core.trace import get_trace_id
from app.models.audit_event import AuditEvent
from app.repositories.audit_event_repository import (
    create_audit_event,
    list_audit_events,
)


def record_audit_event(
    db: Session,
    *,
    event_type: str,
    actor_user_id: UUID | None = None,
    entity_type: str | None = None,
    entity_id: UUID | None = None,
    action: str | None = None,
    old_values: dict | None = None,
    new_values: dict | None = None,
    metadata: dict | None = None,
    trace_id: UUID | None = None,
) -> AuditEvent:

    event = AuditEvent(
        trace_id=(trace_id or get_trace_id()),
        actor_user_id=actor_user_id,
        event_type=getattr(event_type, "value", event_type),
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        old_values=(
            sanitize_audit_value(jsonable_encoder(old_values))
            if old_values is not None
            else None
        ),
        new_values=(
            sanitize_audit_value(jsonable_encoder(new_values))
            if new_values is not None
            else None
        ),
        event_metadata=(
            sanitize_audit_value(jsonable_encoder(metadata))
            if metadata is not None
            else None
        ),
    )

    return create_audit_event(
        db,
        event,
    )


def get_recent_audit_events(
    db: Session,
    limit: int = 100,
) -> list[AuditEvent]:

    return list_audit_events(
        db,
        limit=limit,
    )
