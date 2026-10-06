from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.monitoring_run import MonitoringRun


def get_monitoring_run_by_id(
    db: Session,
    monitoring_run_id: UUID,
) -> MonitoringRun | None:

    return db.get(
        MonitoringRun,
        monitoring_run_id,
    )


def list_monitoring_runs(
    db: Session,
) -> list[MonitoringRun]:

    statement = select(MonitoringRun).order_by(MonitoringRun.created_at.desc())

    return list(db.scalars(statement).all())


def create_monitoring_run(
    db: Session,
    monitoring_run: MonitoringRun,
) -> MonitoringRun:

    db.add(monitoring_run)
    db.flush()

    return monitoring_run


def get_latest_monitoring_run(db: Session) -> MonitoringRun | None:
    statement = select(MonitoringRun).order_by(MonitoringRun.created_at.desc()).limit(1)
    return db.scalar(statement)
