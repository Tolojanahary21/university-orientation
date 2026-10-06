from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.field import Field


def get_field_by_id(
    db: Session,
    field_id: UUID,
) -> Field | None:

    return db.get(
        Field,
        field_id,
    )


def get_active_field_by_id(
    db: Session,
    field_id: UUID,
) -> Field | None:

    statement = select(Field).where(
        Field.id == field_id,
        Field.is_active.is_(True),
    )

    return db.scalar(statement)


def get_field_by_code(
    db: Session,
    code: str,
) -> Field | None:

    statement = select(Field).where(Field.code == code)

    return db.scalar(statement)


def get_active_fields(
    db: Session,
) -> list[Field]:

    statement = select(Field).where(Field.is_active.is_(True)).order_by(Field.name)

    return list(db.scalars(statement).all())


def create_field(
    db: Session,
    field: Field,
) -> Field:

    db.add(field)
    db.flush()

    return field


def save_field(
    db: Session,
    field: Field,
) -> Field:

    db.flush()

    return field


def count_active_fields(db: Session) -> int:
    from sqlalchemy import func

    return db.scalar(select(func.count(Field.id)).where(Field.is_active.is_(True))) or 0
