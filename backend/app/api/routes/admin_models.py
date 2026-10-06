from uuid import UUID

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
from app.schemas.model_version import (
    ModelStatusUpdate,
    ModelVersionCreate,
    ModelVersionResponse,
    ModelVersionUpdate,
)
from app.services.model_version_service import (
    MLflowRunAlreadyExistsError,
    ModelVersionAlreadyExistsError,
    ModelVersionNotFoundError,
    ParentModelNotFoundError,
    change_model_status,
    get_all_model_versions,
    get_model_version,
    register_model_version,
    update_model_version,
)

router = APIRouter(
    prefix="/admin/models",
    tags=["Admin Models"],
)


@router.get(
    "",
    response_model=list[ModelVersionResponse],
)
def list_models(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    return get_all_model_versions(db)


@router.get(
    "/{model_id}",
    response_model=ModelVersionResponse,
)
def get_model(
    model_id: UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    try:
        return get_model_version(
            db,
            model_id,
        )

    except ModelVersionNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Version de modèle introuvable.",
        )


@router.post(
    "",
    response_model=ModelVersionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_model(
    data: ModelVersionCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    try:
        return register_model_version(
            db,
            data,
            actor=admin,
        )

    except ModelVersionAlreadyExistsError:
        raise HTTPException(
            status_code=409,
            detail=("Cette version de modèle existe déjà."),
        )

    except MLflowRunAlreadyExistsError:
        raise HTTPException(
            status_code=409,
            detail=("Ce run MLflow est déjà associé à un modèle."),
        )

    except ParentModelNotFoundError:
        raise HTTPException(
            status_code=400,
            detail="Modèle parent introuvable.",
        )


@router.patch(
    "/{model_id}",
    response_model=ModelVersionResponse,
)
def update_model(
    model_id: UUID,
    data: ModelVersionUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    try:
        return update_model_version(
            db,
            model_id,
            data,
            actor=admin,
        )

    except ModelVersionNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Version de modèle introuvable.",
        )

    except MLflowRunAlreadyExistsError:
        raise HTTPException(
            status_code=409,
            detail=("Ce run MLflow est déjà associé à un modèle."),
        )


@router.patch(
    "/{model_id}/status",
    response_model=ModelVersionResponse,
)
def update_model_status(
    model_id: UUID,
    data: ModelStatusUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    try:
        return change_model_status(
            db,
            model_id,
            data,
            actor=admin,
        )

    except ModelVersionNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Version de modèle introuvable.",
        )
