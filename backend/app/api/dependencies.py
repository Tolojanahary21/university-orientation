import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from collections.abc import Generator

from app.db.session import SessionLocal
from app.models.user import User
from app.repositories.user_repository import get_user_by_id
from app.services.token_service import decode_access_token


security = HTTPBearer(
    auto_error=False
)

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials
    | None = Depends(security),
    db: Session = Depends(get_db),
) -> User:

    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Authentification requise.",
        )

    try:
        user_id = decode_access_token(
            credentials.credentials
        )

    except (
        jwt.InvalidTokenError,
        ValueError,
    ):
        raise HTTPException(
            status_code=401,
            detail="Token invalide.",
        )

    user = get_user_by_id(
        db,
        user_id,
    )

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Utilisateur introuvable.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Compte désactivé.",
        )

    return user
