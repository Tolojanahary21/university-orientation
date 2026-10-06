from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, require_admin
from app.models.user import User
from app.schemas.admin_stats import AdminStatsResponse
from app.services.admin_stats_service import get_admin_stats

router = APIRouter(prefix="/admin/stats", tags=["Admin Stats"])


@router.get("", response_model=AdminStatsResponse)
def admin_stats(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    return get_admin_stats(db)
