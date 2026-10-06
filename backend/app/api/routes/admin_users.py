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
from app.schemas.auth import (
    AdminCreateUserRequest,
)
from app.schemas.user import UserResponse
from app.services.auth_service import (
    EmailAlreadyExistsError,
    EmailSendError,
    create_user_by_admin,
)

router = APIRouter(
    prefix="/admin/users",
    tags=["Admin Users"],
)


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user(
    data: AdminCreateUserRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    try:
        return create_user_by_admin(
            db,
            data,
        )

    except EmailAlreadyExistsError:
        raise HTTPException(
            status_code=409,
            detail="Un compte existe déjà avec cet e-mail.",
        )

    except EmailSendError:
        raise HTTPException(
            status_code=503,
            detail=(
                "Utilisateur créé, mais l'e-mail "
                "de vérification n'a pas pu être envoyé."
            ),
        )
