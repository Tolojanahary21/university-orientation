from datetime import datetime
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from app.models.enums import (
    Environment,
    ModelStatus,
    TrainingType,
)


class ModelVersionCreate(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=150,
    )

    version: str = Field(
        min_length=1,
        max_length=30,
    )

    algorithm: str | None = Field(
        default=None,
        max_length=100,
    )

    status: ModelStatus = ModelStatus.CANDIDATE

    training_type: TrainingType

    parent_model_id: UUID | None = None

    mlflow_run_id: str | None = Field(
        default=None,
        max_length=255,
    )

    mlflow_model_uri: str | None = None

    dvc_revision: str | None = Field(
        default=None,
        max_length=255,
    )

    dataset_path: str | None = None

    git_commit_sha: str | None = Field(
        default=None,
        max_length=40,
    )

    feature_schema_version: str | None = Field(
        default=None,
        max_length=30,
    )

    metrics: dict | None = None

    model_signature: dict | None = None

    docker_image: str | None = Field(
        default=None,
        max_length=255,
    )

    docker_tag: str | None = Field(
        default=None,
        max_length=100,
    )

    docker_digest: str | None = None

    environment: Environment = Environment.DEVELOPMENT

    retraining_reason: str | None = None


class ModelVersionUpdate(BaseModel):
    algorithm: str | None = Field(
        default=None,
        max_length=100,
    )

    mlflow_run_id: str | None = Field(
        default=None,
        max_length=255,
    )

    mlflow_model_uri: str | None = None

    dvc_revision: str | None = Field(
        default=None,
        max_length=255,
    )

    dataset_path: str | None = None

    git_commit_sha: str | None = Field(
        default=None,
        max_length=40,
    )

    feature_schema_version: str | None = Field(
        default=None,
        max_length=30,
    )

    metrics: dict | None = None

    model_signature: dict | None = None

    docker_image: str | None = Field(
        default=None,
        max_length=255,
    )

    docker_tag: str | None = Field(
        default=None,
        max_length=100,
    )

    docker_digest: str | None = None

    environment: Environment | None = None

    retraining_reason: str | None = None


class ModelStatusUpdate(BaseModel):
    status: ModelStatus


class ModelVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID

    name: str
    version: str
    algorithm: str | None

    status: ModelStatus
    training_type: TrainingType

    parent_model_id: UUID | None

    mlflow_run_id: str | None
    mlflow_model_uri: str | None

    dvc_revision: str | None
    dataset_path: str | None

    git_commit_sha: str | None

    feature_schema_version: str | None

    metrics: dict | None
    model_signature: dict | None

    docker_image: str | None
    docker_tag: str | None
    docker_digest: str | None

    environment: Environment

    retraining_reason: str | None

    created_at: datetime
    validated_at: datetime | None
    deployed_at: datetime | None
    archived_at: datetime | None
