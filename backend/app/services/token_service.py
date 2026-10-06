from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt

from app.core.config import (
    JWT_ACCESS_TOKEN_MINUTES,
    JWT_ALGORITHM,
    JWT_SECRET_KEY,
)


def create_access_token(
    user_id: UUID,
) -> str:

    now = datetime.now(UTC)

    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=JWT_ACCESS_TOKEN_MINUTES),
    }

    return jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )


def decode_access_token(
    token: str,
) -> UUID:

    payload = jwt.decode(
        token,
        JWT_SECRET_KEY,
        algorithms=[JWT_ALGORITHM],
    )

    return UUID(payload["sub"])
