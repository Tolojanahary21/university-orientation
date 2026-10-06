from uuid import UUID

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
from app.schemas.recommendation import (
    RecommendationFeedbackRequest,
    RecommendationResponse,
)
from app.services.recommendation_service import (
    FeedbackAlreadyExistsError,
    RecommendationNotFoundError,
    add_recommendation_feedback,
)

router = APIRouter(
    prefix="/recommendations",
    tags=["Recommendations"],
)


@router.post(
    "/{recommendation_id}/feedback",
    response_model=RecommendationResponse,
)
def add_feedback(
    recommendation_id: UUID,
    data: RecommendationFeedbackRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return add_recommendation_feedback(
            db=db,
            recommendation_id=(recommendation_id),
            current_user=current_user,
            data=data,
        )

    except RecommendationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recommandation introuvable.",
        )

    except FeedbackAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=("Un feedback a déjà été enregistré pour cette recommandation."),
        )
