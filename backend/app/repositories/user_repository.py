from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


def normalize_email(email: str) -> str:
    return email.strip().lower()


def get_user_by_email(
    db: Session,
    email: str,
    *,
    for_update: bool = False,
) -> User | None:

    statement = select(User).where(User.email == normalize_email(email))

    if for_update:
        statement = statement.with_for_update()

    return db.scalar(statement)


def get_user_by_id(
    db: Session,
    user_id: UUID,
) -> User | None:

    return db.get(User, user_id)


def count_users(db: Session) -> int:
    from sqlalchemy import func

    return db.scalar(select(func.count(User.id))) or 0
