from pydantic import BaseModel

from app.schemas.model_version import ModelVersionResponse
from app.schemas.monitoring_run import MonitoringRunResponse


class RecommendationStats(BaseModel):
    total: int
    success: int
    failed: int
    pending: int
    average_latency_ms: float | None


class AdminStatsResponse(BaseModel):
    users_count: int
    active_fields_count: int
    recommendations: RecommendationStats
    production_model: ModelVersionResponse | None
    latest_monitoring_run: MonitoringRunResponse | None
