from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.student_profile import StudentProfile


def get_profile_by_user_id(
    db: Session,
    user_id: UUID,
) -> StudentProfile | None:
    statement = select(StudentProfile).where(StudentProfile.user_id == user_id)

    return db.scalar(statement)


def get_profile_by_id(
    db: Session,
    profile_id: UUID,
) -> StudentProfile | None:
    return db.get(
        StudentProfile,
        profile_id,
    )


def create_profile(
    db: Session,
    profile: StudentProfile,
) -> StudentProfile:
    db.add(profile)
    db.flush()

    return profile


def save_profile(
    db: Session,
    profile: StudentProfile,
) -> StudentProfile:
    db.flush()

    return profile
