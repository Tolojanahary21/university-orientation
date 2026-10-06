from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.audit_events import AuditEventType
from app.models.enums import ModelStatus
from app.models.model_version import ModelVersion
from app.models.user import User
from app.repositories.model_version_repository import (
    create_model_version,
    get_model_version_by_id,
    get_model_version_by_mlflow_run_id,
    get_model_version_by_version,
    list_model_versions,
    save_model_version,
)
from app.schemas.model_version import (
    ModelStatusUpdate,
    ModelVersionCreate,
    ModelVersionUpdate,
)
from app.services.audit_event_service import record_audit_event


class ModelVersionNotFoundError(Exception):
    pass


class ModelVersionAlreadyExistsError(Exception):
    pass


class MLflowRunAlreadyExistsError(Exception):
    pass


class ParentModelNotFoundError(Exception):
    pass


def get_all_model_versions(
    db: Session,
) -> list[ModelVersion]:

    return list_model_versions(db)


def get_model_version(
    db: Session,
    model_id: UUID,
) -> ModelVersion:

    model = get_model_version_by_id(
        db,
        model_id,
    )

    if model is None:
        raise ModelVersionNotFoundError()

    return model


def register_model_version(
    db: Session,
    data: ModelVersionCreate,
    actor: User | None = None,
) -> ModelVersion:

    existing_version = get_model_version_by_version(
        db,
        data.version,
    )

    if existing_version is not None:
        raise ModelVersionAlreadyExistsError()

    if data.mlflow_run_id is not None:
        existing_mlflow = get_model_version_by_mlflow_run_id(
            db,
            data.mlflow_run_id,
        )

        if existing_mlflow is not None:
            raise MLflowRunAlreadyExistsError()

    if data.parent_model_id is not None:
        parent = get_model_version_by_id(
            db,
            data.parent_model_id,
        )

        if parent is None:
            raise ParentModelNotFoundError()

    model = ModelVersion(
        name=data.name,
        version=data.version,
        algorithm=data.algorithm,
        status=data.status,
        training_type=data.training_type,
        parent_model_id=data.parent_model_id,
        mlflow_run_id=data.mlflow_run_id,
        mlflow_model_uri=data.mlflow_model_uri,
        dvc_revision=data.dvc_revision,
        dataset_path=data.dataset_path,
        git_commit_sha=data.git_commit_sha,
        feature_schema_version=(data.feature_schema_version),
        metrics=data.metrics,
        model_signature=data.model_signature,
        docker_image=data.docker_image,
        docker_tag=data.docker_tag,
        docker_digest=data.docker_digest,
        environment=data.environment,
        retraining_reason=data.retraining_reason,
    )

    create_model_version(db, model)
    record_audit_event(
        db,
        event_type=AuditEventType.MODEL_REGISTERED,
        actor_user_id=actor.id if actor else None,
        entity_type="model_version",
        entity_id=model.id,
        action="register",
        new_values={
            "name": model.name,
            "version": model.version,
            "status": model.status.value,
        },
    )
    db.commit()
    db.refresh(model)
    return model


def update_model_version(
    db: Session,
    model_id: UUID,
    data: ModelVersionUpdate,
    actor: User | None = None,
) -> ModelVersion:

    model = get_model_version_by_id(
        db,
        model_id,
    )

    if model is None:
        raise ModelVersionNotFoundError()

    update_data = data.model_dump(exclude_unset=True)

    if "mlflow_run_id" in update_data and update_data["mlflow_run_id"] is not None:
        existing = get_model_version_by_mlflow_run_id(
            db,
            update_data["mlflow_run_id"],
        )

        if existing is not None and existing.id != model.id:
            raise MLflowRunAlreadyExistsError()

    changed = False
    old_values = {}

    for field_name, new_value in update_data.items():
        old_value = getattr(
            model,
            field_name,
        )

        if old_value != new_value:
            old_values[field_name] = old_value
            setattr(
                model,
                field_name,
                new_value,
            )

            changed = True

    if changed:
        save_model_version(db, model)
        record_audit_event(
            db,
            event_type=AuditEventType.MODEL_PROMOTED,
            actor_user_id=actor.id if actor else None,
            entity_type="model_version",
            entity_id=model.id,
            action="update",
            old_values=old_values,
            new_values={key: getattr(model, key) for key in old_values},
        )
        db.commit()
        db.refresh(model)
        return model

    return model


def change_model_status(
    db: Session,
    model_id: UUID,
    data: ModelStatusUpdate,
    actor: User | None = None,
) -> ModelVersion:

    model = get_model_version_by_id(
        db,
        model_id,
    )

    if model is None:
        raise ModelVersionNotFoundError()

    if model.status == data.status:
        return model

    now = datetime.now(UTC)
    old_status = model.status

    model.status = data.status

    if data.status == ModelStatus.VALIDATED:
        model.validated_at = now

    elif data.status == ModelStatus.PRODUCTION:
        model.deployed_at = now

    elif data.status == ModelStatus.ARCHIVED:
        model.archived_at = now

    save_model_version(db, model)
    event_type = {
        ModelStatus.VALIDATED: AuditEventType.MODEL_VALIDATED,
        ModelStatus.REJECTED: AuditEventType.MODEL_REJECTED,
        ModelStatus.PRODUCTION: AuditEventType.MODEL_DEPLOYED,
        ModelStatus.ARCHIVED: AuditEventType.MODEL_ARCHIVED,
    }.get(data.status, AuditEventType.MODEL_PROMOTED)
    record_audit_event(
        db,
        event_type=event_type,
        actor_user_id=actor.id if actor else None,
        entity_type="model_version",
        entity_id=model.id,
        action="status_change",
        old_values={"status": old_status.value},
        new_values={"status": model.status.value},
    )
    db.commit()
    db.refresh(model)
    return model
