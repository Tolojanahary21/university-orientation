from sqlalchemy.orm import Session

from app.core.audit_events import AuditEventType
from app.models.student_profile import StudentProfile
from app.models.user import User
from app.repositories.profile_repository import (
    create_profile,
    get_profile_by_user_id,
    save_profile,
)
from app.schemas.profile import (
    StudentProfileCreate,
    StudentProfileUpdate,
)
from app.services.audit_event_service import (
    record_audit_event,
)


class ProfileAlreadyExistsError(Exception):
    pass


class ProfileNotFoundError(Exception):
    pass


def create_student_profile(
    db: Session,
    current_user: User,
    data: StudentProfileCreate,
) -> StudentProfile:

    existing_profile = get_profile_by_user_id(
        db,
        current_user.id,
    )

    if existing_profile is not None:
        raise ProfileAlreadyExistsError()

    profile = StudentProfile(
        user_id=current_user.id,
        bac_series=data.bac_series,
        graduation_year=data.graduation_year,
        scores=data.scores,
        average_score=data.average_score,
        mention=data.mention,
        preferences=data.preferences,
        profile_version=1,
    )

    create_profile(db, profile)
    record_audit_event(
        db,
        event_type=AuditEventType.PROFILE_CREATED,
        actor_user_id=current_user.id,
        entity_type="student_profile",
        entity_id=profile.id,
        action="create",
        new_values={
            "bac_series": profile.bac_series,
            "graduation_year": profile.graduation_year,
        },
    )
    db.commit()
    db.refresh(profile)
    return profile


def get_current_student_profile(
    db: Session,
    current_user: User,
) -> StudentProfile:

    profile = get_profile_by_user_id(
        db,
        current_user.id,
    )

    if profile is None:
        raise ProfileNotFoundError()

    return profile


def update_student_profile(
    db: Session,
    current_user: User,
    data: StudentProfileUpdate,
) -> StudentProfile:

    profile = get_profile_by_user_id(
        db,
        current_user.id,
    )

    if profile is None:
        raise ProfileNotFoundError()

    update_data = data.model_dump(exclude_unset=True)

    has_changes = False
    old_values = {}

    for field, new_value in update_data.items():
        current_value = getattr(
            profile,
            field,
        )

        if current_value != new_value:
            old_values[field] = current_value
            setattr(
                profile,
                field,
                new_value,
            )

            has_changes = True

    if has_changes:
        profile.profile_version += 1

        save_profile(db, profile)
        record_audit_event(
            db,
            event_type=AuditEventType.PROFILE_UPDATED,
            actor_user_id=current_user.id,
            entity_type="student_profile",
            entity_id=profile.id,
            action="update",
            old_values=old_values,
            new_values={key: getattr(profile, key) for key in old_values},
        )
        db.commit()
        db.refresh(profile)
        return profile

    return profile
