from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import ModelStatus
from app.models.model_version import ModelVersion


def get_model_version_by_id(
    db: Session,
    model_id: UUID,
) -> ModelVersion | None:

    return db.get(
        ModelVersion,
        model_id,
    )


def get_model_version_by_version(
    db: Session,
    version: str,
) -> ModelVersion | None:

    statement = select(ModelVersion).where(ModelVersion.version == version)

    return db.scalar(statement)


def get_model_version_by_mlflow_run_id(
    db: Session,
    mlflow_run_id: str,
) -> ModelVersion | None:

    statement = select(ModelVersion).where(ModelVersion.mlflow_run_id == mlflow_run_id)

    return db.scalar(statement)


def list_model_versions(
    db: Session,
) -> list[ModelVersion]:

    statement = select(ModelVersion).order_by(ModelVersion.created_at.desc())

    return list(db.scalars(statement).all())


def get_production_model(
    db: Session,
) -> ModelVersion | None:

    statement = (
        select(ModelVersion)
        .where(ModelVersion.status == ModelStatus.PRODUCTION)
        .order_by(ModelVersion.deployed_at.desc())
    )

    return db.scalars(statement).first()


def create_model_version(
    db,
    model: ModelVersion,
) -> ModelVersion:

    db.add(model)
    db.flush()

    return model


def save_model_version(
    db: Session,
    model: ModelVersion,
) -> ModelVersion:

    db.flush()

    return model
