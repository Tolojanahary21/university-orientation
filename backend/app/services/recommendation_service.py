import hashlib
import json
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.audit_events import AuditEventType
from app.models.enums import (
    RecommendationSource,
    RecommendationStatus,
)
from app.models.recommendation import Recommendation
from app.models.user import User
from app.repositories.recommendation_repository import (
    create_recommendation,
    get_recommendation_for_user,
    save_recommendation,
)
from app.schemas.recommendation import (
    RecommendationFeedbackRequest,
)
from app.services.audit_event_service import record_audit_event


class RecommendationNotFoundError(Exception):
    pass


class FeedbackAlreadyExistsError(Exception):
    pass


def build_input_hash(
    snapshot: dict,
) -> str:

    serialized = json.dumps(
        snapshot,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )

    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def start_recommendation(
    db: Session,
    student_profile_id: UUID,
    model_version_id: UUID,
    input_snapshot: dict,
    source: RecommendationSource,
) -> Recommendation:

    recommendation = Recommendation(
        student_profile_id=student_profile_id,
        model_version_id=model_version_id,
        input_snapshot=input_snapshot,
        input_hash=build_input_hash(input_snapshot),
        results=None,
        top_field_id=None,
        status=RecommendationStatus.PENDING,
        latency_ms=None,
        source=source,
    )

    create_recommendation(db, recommendation)
    record_audit_event(
        db,
        event_type=AuditEventType.RECOMMENDATION_CREATED,
        entity_type="recommendation",
        entity_id=recommendation.id,
        action="create",
        new_values={
            "status": recommendation.status.value,
            "source": recommendation.source.value,
        },
    )
    db.commit()
    db.refresh(recommendation)
    return recommendation


def complete_recommendation(
    db: Session,
    recommendation: Recommendation,
    results: dict | list,
    top_field_id: UUID | None,
    latency_ms: int,
) -> Recommendation:

    recommendation.results = results
    recommendation.top_field_id = top_field_id

    recommendation.status = RecommendationStatus.SUCCESS

    recommendation.latency_ms = latency_ms

    recommendation.error_code = None
    recommendation.error_message = None

    recommendation.completed_at = datetime.now(UTC)

    save_recommendation(db, recommendation)
    db.commit()
    db.refresh(recommendation)
    return recommendation


def fail_recommendation(
    db: Session,
    recommendation: Recommendation,
    error_code: str,
    error_message: str,
    latency_ms: int | None = None,
) -> Recommendation:
    recommendation.status = RecommendationStatus.FAILED
    recommendation.error_code = error_code
    recommendation.error_message = error_message
    recommendation.latency_ms = latency_ms
    recommendation.completed_at = datetime.now(UTC)
    save_recommendation(db, recommendation)
    db.commit()
    db.refresh(recommendation)
    return recommendation


def add_recommendation_feedback(
    db: Session,
    recommendation_id: UUID,
    current_user: User,
    data: RecommendationFeedbackRequest,
) -> Recommendation:

    recommendation = get_recommendation_for_user(
        db,
        recommendation_id,
        current_user.id,
    )

    if recommendation is None:
        raise RecommendationNotFoundError()

    if recommendation.feedback_rating is not None:
        raise FeedbackAlreadyExistsError()

    recommendation.feedback_rating = data.rating

    recommendation.feedback_comment = data.comment

    save_recommendation(db, recommendation)
    record_audit_event(
        db,
        event_type=AuditEventType.RECOMMENDATION_FEEDBACK_ADDED,
        actor_user_id=current_user.id,
        entity_type="recommendation",
        entity_id=recommendation.id,
        action="feedback",
        new_values={
            "feedback_rating": data.rating,
            "feedback_comment": data.comment,
        },
    )
    db.commit()
    db.refresh(recommendation)
    return recommendation
