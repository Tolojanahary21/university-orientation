from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.recommendation import Recommendation
from app.models.student_profile import StudentProfile


def get_recommendation_by_id(
    db: Session,
    recommendation_id: UUID,
) -> Recommendation | None:

    return db.get(
        Recommendation,
        recommendation_id,
    )


def get_recommendation_for_user(
    db: Session,
    recommendation_id: UUID,
    user_id: UUID,
) -> Recommendation | None:

    statement = (
        select(Recommendation)
        .join(
            StudentProfile,
            Recommendation.student_profile_id == StudentProfile.id,
        )
        .where(
            Recommendation.id == recommendation_id,
            StudentProfile.user_id == user_id,
        )
    )

    return db.scalar(statement)


def create_recommendation(
    db: Session,
    recommendation: Recommendation,
) -> Recommendation:

    db.add(recommendation)
    db.flush()

    return recommendation


def save_recommendation(
    db: Session,
    recommendation: Recommendation,
) -> Recommendation:

    db.flush()

    return recommendation


def recommendation_statistics(db: Session) -> dict:
    from sqlalchemy import func

    from app.models.enums import RecommendationStatus

    statement = select(
        Recommendation.status,
        func.count(Recommendation.id),
        func.avg(Recommendation.latency_ms),
    ).group_by(Recommendation.status)
    rows = db.execute(statement).all()
    counts = {status.value: count for status, count, _ in rows}
    latencies = [float(avg) for _, _, avg in rows if avg is not None]
    return {
        "total": sum(counts.values()),
        "success": counts.get(RecommendationStatus.SUCCESS.value, 0),
        "failed": counts.get(RecommendationStatus.FAILED.value, 0),
        "pending": counts.get(RecommendationStatus.PENDING.value, 0),
        "average_latency_ms": (sum(latencies) / len(latencies) if latencies else None),
    }
