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
from app.schemas.field import (
    FieldCreate,
    FieldResponse,
    FieldUpdate,
)
from app.services.field_service import (
    FieldCodeAlreadyExistsError,
    FieldNotFoundError,
    create_catalog_field,
    deactivate_catalog_field,
    get_public_field,
    list_active_fields,
    update_catalog_field,
)

router = APIRouter(
    prefix="/fields",
    tags=["Fields"],
)


@router.get(
    "",
    response_model=list[FieldResponse],
)
def get_fields(
    db: Session = Depends(get_db),
):
    return list_active_fields(db)


@router.get(
    "/{field_id}",
    response_model=FieldResponse,
)
def get_field(
    field_id: UUID,
    db: Session = Depends(get_db),
):
    try:
        return get_public_field(
            db,
            field_id,
        )

    except FieldNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Filière introuvable.",
        )


@router.post(
    "",
    response_model=FieldResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_new_field(
    data: FieldCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    try:
        return create_catalog_field(
            db,
            data,
            actor=admin,
        )

    except FieldCodeAlreadyExistsError:
        raise HTTPException(
            status_code=409,
            detail=("Une filière possède déjà ce code."),
        )


@router.put(
    "/{field_id}",
    response_model=FieldResponse,
)
def update_field(
    field_id: UUID,
    data: FieldUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    try:
        return update_catalog_field(
            db,
            field_id,
            data,
            actor=admin,
        )

    except FieldNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Filière introuvable.",
        )

    except FieldCodeAlreadyExistsError:
        raise HTTPException(
            status_code=409,
            detail=("Une filière possède déjà ce code."),
        )


@router.patch(
    "/{field_id}/deactivate",
    response_model=FieldResponse,
)
def deactivate_field(
    field_id: UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    try:
        return deactivate_catalog_field(
            db,
            field_id,
            actor=admin,
        )

    except FieldNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Filière introuvable.",
        )
