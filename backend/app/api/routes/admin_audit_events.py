from fastapi import (
    APIRouter,
    Depends,
    Query,
)
from sqlalchemy.orm import Session

from app.api.dependencies import (
    get_db,
    require_admin,
)
from app.models.user import User
from app.schemas.audit_event import (
    AuditEventResponse,
)
from app.services.audit_event_service import (
    get_recent_audit_events,
)

router = APIRouter(
    prefix="/admin/audit-events",
    tags=["Admin Audit"],
)


@router.get(
    "",
    response_model=list[AuditEventResponse],
)
def get_audit_events(
    limit: int = Query(
        default=100,
        ge=1,
        le=500,
    ),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    return get_recent_audit_events(
        db,
        limit=limit,
    )
