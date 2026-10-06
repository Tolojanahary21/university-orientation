from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.repositories.model_version_repository import get_production_model
from app.schemas.model_info import ModelInfoResponse

router = APIRouter(prefix="/model", tags=["Model Info"])


@router.get("/info", response_model=ModelInfoResponse)
def model_info(db: Session = Depends(get_db)):
    model = get_production_model(db)
    if model is None:
        raise HTTPException(status_code=404, detail="Aucun mod?le en production.")
    return model
