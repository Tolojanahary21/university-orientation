from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from app.api.dependencies import (
    get_current_user,
    get_db,
)
from app.models.user import User
from app.schemas.profile import (
    StudentProfileCreate,
    StudentProfileResponse,
    StudentProfileUpdate,
)
from app.services.profile_service import (
    ProfileAlreadyExistsError,
    ProfileNotFoundError,
    create_student_profile,
    get_current_student_profile,
    update_student_profile,
)

router = APIRouter(
    prefix="/profiles",
    tags=["Student Profiles"],
)


@router.post(
    "",
    response_model=StudentProfileResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_profile(
    data: StudentProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return create_student_profile(
            db=db,
            current_user=current_user,
            data=data,
        )

    except ProfileAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Un profil étudiant existe déjà pour cet utilisateur.",
        )


@router.get(
    "/me",
    response_model=StudentProfileResponse,
)
def get_my_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return get_current_student_profile(
            db=db,
            current_user=current_user,
        )

    except ProfileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profil étudiant introuvable.",
        )


@router.put(
    "/me",
    response_model=StudentProfileResponse,
)
def update_my_profile(
    data: StudentProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return update_student_profile(
            db=db,
            current_user=current_user,
            data=data,
        )

    except ProfileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profil étudiant introuvable.",
        )
