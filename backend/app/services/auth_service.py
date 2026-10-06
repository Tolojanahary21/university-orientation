from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.enums import UserRole
from app.models.user import User
from app.repositories.user_repository import (
    get_user_by_email,
    normalize_email,
)
from app.schemas.auth import RegisterRequest
from app.services.email_service import (
    EmailDeliveryError,
    send_verification_email,
)
from app.services.otp_service import (
    create_email_verification_otp,
)
from app.services.password_service import (
    hash_password,
    verify_password,
)


class EmailAlreadyExistsError(Exception):
    pass


class EmailNotVerifiedError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


class AccountDisabledError(Exception):
    pass


class EmailSendError(Exception):
    pass


def register_user(
    db: Session,
    data: RegisterRequest,
) -> User:

    email = normalize_email(
        str(data.email)
    )

    existing_user = get_user_by_email(
        db,
        email,
    )

    if existing_user is not None:
        raise EmailAlreadyExistsError()

    user = User(
        email=email,
        password_hash=hash_password(
            data.password
        ),
        first_name=data.first_name,
        last_name=data.last_name,
        role=UserRole.STUDENT,
    )

    db.add(user)

    # nécessaire pour obtenir user.id
    db.flush()

    otp = create_email_verification_otp(
        user
    )

    db.commit()
    db.refresh(user)

    try:
        send_verification_email(
            user.email,
            otp,
        )

    except EmailDeliveryError:
        # Le compte reste créé et non vérifié.
        # L'utilisateur pourra faire resend-otp.
        raise EmailSendError()

    return user


def authenticate_user(
    db: Session,
    email: str,
    password: str,
) -> User:

    user = get_user_by_email(
        db,
        email,
    )

    if user is None:
        raise InvalidCredentialsError()

    if not verify_password(
        password,
        user.password_hash,
    ):
        raise InvalidCredentialsError()

    if not user.is_active:
        raise AccountDisabledError()

    if user.email_verified_at is None:
        raise EmailNotVerifiedError()

    user.last_login_at = datetime.now(
        timezone.utc
    )

    db.commit()
    db.refresh(user)

    return user