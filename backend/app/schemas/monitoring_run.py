from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import Environment


class MonitoringRunCreate(BaseModel):
    model_version_id: UUID

    environment: Environment

    reference_dvc_revision: str | None = None

    period_start: datetime
    period_end: datetime

    sample_count: int

    data_drift_detected: bool
    prediction_drift_detected: bool

    data_drift_score: Decimal | None = None
    prediction_drift_score: Decimal | None = None

    feature_drift: dict | None = None
    data_quality: dict | None = None
    prediction_distribution: dict | None = None
    performance_metrics: dict | None = None

    report_uri: str | None = None


class MonitoringRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    model_version_id: UUID

    environment: Environment

    reference_dvc_revision: str | None

    period_start: datetime
    period_end: datetime

    sample_count: int

    data_drift_detected: bool
    prediction_drift_detected: bool

    data_drift_score: Decimal | None
    prediction_drift_score: Decimal | None

    feature_drift: dict | None
    data_quality: dict | None
    prediction_distribution: dict | None
    performance_metrics: dict | None

    report_uri: str | None

    created_at: datetime
