from sqlalchemy.orm import Session

from app.core.audit_events import AuditEventType
from app.models.monitoring_run import MonitoringRun
from app.models.user import User
from app.repositories.model_version_repository import (
    get_model_version_by_id,
)
from app.repositories.monitoring_run_repository import (
    create_monitoring_run,
    list_monitoring_runs,
)
from app.schemas.monitoring_run import (
    MonitoringRunCreate,
)
from app.services.audit_event_service import record_audit_event


class MonitoringModelNotFoundError(Exception):
    pass


def get_all_monitoring_runs(
    db: Session,
) -> list[MonitoringRun]:

    return list_monitoring_runs(db)


def record_monitoring_run(
    db: Session,
    data: MonitoringRunCreate,
    actor: User | None = None,
) -> MonitoringRun:

    model = get_model_version_by_id(
        db,
        data.model_version_id,
    )

    if model is None:
        raise MonitoringModelNotFoundError()

    monitoring_run = MonitoringRun(
        model_version_id=data.model_version_id,
        environment=data.environment,
        reference_dvc_revision=(data.reference_dvc_revision),
        period_start=data.period_start,
        period_end=data.period_end,
        sample_count=data.sample_count,
        data_drift_detected=(data.data_drift_detected),
        prediction_drift_detected=(data.prediction_drift_detected),
        data_drift_score=(data.data_drift_score),
        prediction_drift_score=(data.prediction_drift_score),
        feature_drift=data.feature_drift,
        data_quality=data.data_quality,
        prediction_distribution=(data.prediction_distribution),
        performance_metrics=(data.performance_metrics),
        report_uri=data.report_uri,
    )

    create_monitoring_run(db, monitoring_run)
    if data.data_drift_detected or data.prediction_drift_detected:
        record_audit_event(
            db,
            event_type=AuditEventType.DRIFT_DETECTED,
            actor_user_id=actor.id if actor else None,
            entity_type="monitoring_run",
            entity_id=monitoring_run.id,
            action="drift_detected",
            new_values={
                "data_drift_detected": data.data_drift_detected,
                "prediction_drift_detected": data.prediction_drift_detected,
            },
        )
    db.commit()
    db.refresh(monitoring_run)
    return monitoring_run
