from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from app.api.dependencies import (
    get_db,
    require_admin,
)
from app.models.user import User
from app.schemas.monitoring_run import (
    MonitoringRunCreate,
    MonitoringRunResponse,
)
from app.services.monitoring_run_service import (
    MonitoringModelNotFoundError,
    get_all_monitoring_runs,
    record_monitoring_run,
)

router = APIRouter(
    prefix="/admin/monitoring",
    tags=["Admin Monitoring"],
)


@router.get(
    "",
    response_model=list[MonitoringRunResponse],
)
def get_monitoring(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    return get_all_monitoring_runs(db)


@router.post(
    "",
    response_model=MonitoringRunResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_monitoring(
    data: MonitoringRunCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    try:
        return record_monitoring_run(db, data, actor=admin)
    except MonitoringModelNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Version de modèle introuvable.",
        ) from None
