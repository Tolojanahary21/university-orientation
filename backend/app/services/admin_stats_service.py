from sqlalchemy.orm import Session

from app.repositories.field_repository import count_active_fields
from app.repositories.model_version_repository import get_production_model
from app.repositories.monitoring_run_repository import get_latest_monitoring_run
from app.repositories.recommendation_repository import recommendation_statistics
from app.repositories.user_repository import count_users


def get_admin_stats(db: Session) -> dict:
    return {
        "users_count": count_users(db),
        "active_fields_count": count_active_fields(db),
        "recommendations": recommendation_statistics(db),
        "production_model": get_production_model(db),
        "latest_monitoring_run": get_latest_monitoring_run(db),
    }
