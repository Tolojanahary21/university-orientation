from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit_event import AuditEvent


def create_audit_event(
    db: Session,
    event: AuditEvent,
) -> AuditEvent:

    db.add(event)
    db.flush()

    return event


def get_audit_event_by_id(
    db: Session,
    event_id: UUID,
) -> AuditEvent | None:

    return db.get(
        AuditEvent,
        event_id,
    )


def list_audit_events(
    db: Session,
    limit: int = 100,
) -> list[AuditEvent]:

    statement = select(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(limit)

    return list(db.scalars(statement).all())
