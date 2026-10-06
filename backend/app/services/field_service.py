from uuid import UUID

from sqlalchemy.orm import Session

from app.core.audit_events import AuditEventType
from app.models.field import Field
from app.models.user import User
from app.repositories.field_repository import (
    create_field,
    get_active_field_by_id,
    get_active_fields,
    get_field_by_code,
    get_field_by_id,
    save_field,
)
from app.schemas.field import (
    FieldCreate,
    FieldUpdate,
)
from app.services.audit_event_service import record_audit_event


class FieldNotFoundError(Exception):
    pass


class FieldCodeAlreadyExistsError(Exception):
    pass


def list_active_fields(
    db: Session,
) -> list[Field]:

    return get_active_fields(db)


def get_public_field(
    db: Session,
    field_id: UUID,
) -> Field:

    field = get_active_field_by_id(
        db,
        field_id,
    )

    if field is None:
        raise FieldNotFoundError()

    return field


def create_catalog_field(
    db: Session,
    data: FieldCreate,
    actor: User | None = None,
) -> Field:

    existing = get_field_by_code(
        db,
        data.code,
    )

    if existing is not None:
        raise FieldCodeAlreadyExistsError()

    field = Field(
        code=data.code,
        name=data.name,
        description=data.description,
        category=data.category,
        requirements=data.requirements,
        is_active=True,
    )

    create_field(db, field)
    record_audit_event(
        db,
        event_type=AuditEventType.FIELD_CREATED,
        actor_user_id=actor.id if actor else None,
        entity_type="field",
        entity_id=field.id,
        action="create",
        new_values={
            "code": field.code,
            "name": field.name,
            "is_active": field.is_active,
        },
    )
    db.commit()
    db.refresh(field)
    return field


def update_catalog_field(
    db: Session,
    field_id: UUID,
    data: FieldUpdate,
    actor: User | None = None,
) -> Field:

    field = get_field_by_id(
        db,
        field_id,
    )

    if field is None:
        raise FieldNotFoundError()

    update_data = data.model_dump(exclude_unset=True)

    if "code" in update_data:
        new_code = update_data["code"]

        if new_code != field.code:
            existing = get_field_by_code(
                db,
                new_code,
            )

            if existing is not None:
                raise FieldCodeAlreadyExistsError()

    changed = False
    old_values = {}

    for field_name, new_value in update_data.items():
        old_value = getattr(
            field,
            field_name,
        )

        if old_value != new_value:
            old_values[field_name] = old_value
            setattr(
                field,
                field_name,
                new_value,
            )

            changed = True

    if changed:
        save_field(db, field)
        record_audit_event(
            db,
            event_type=AuditEventType.FIELD_UPDATED,
            actor_user_id=actor.id if actor else None,
            entity_type="field",
            entity_id=field.id,
            action="update",
            old_values=old_values,
            new_values={key: getattr(field, key) for key in update_data},
        )
        db.commit()
        db.refresh(field)
        return field

    return field


def deactivate_catalog_field(
    db: Session,
    field_id: UUID,
    actor: User | None = None,
) -> Field:

    field = get_field_by_id(
        db,
        field_id,
    )

    if field is None:
        raise FieldNotFoundError()

    if not field.is_active:
        return field

    field.is_active = False
    save_field(db, field)
    record_audit_event(
        db,
        event_type=AuditEventType.FIELD_DISABLED,
        actor_user_id=actor.id if actor else None,
        entity_type="field",
        entity_id=field.id,
        action="deactivate",
        old_values={"is_active": True},
        new_values={"is_active": False},
    )
    db.commit()
    db.refresh(field)
    return field
