from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.audit_events import AuditEventType
from app.models.enums import UserRole
from app.models.user import User
from app.repositories.user_repository import (
    get_user_by_email,
    normalize_email,
)
from app.schemas.auth import AdminCreateUserRequest, RegisterRequest
from app.services.audit_event_service import record_audit_event
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

    email = normalize_email(str(data.email))

    existing_user = get_user_by_email(
        db,
        email,
    )

    if existing_user is not None:
        raise EmailAlreadyExistsError()

    user = User(
        email=email,
        password_hash=hash_password(data.password),
        first_name=data.first_name,
        last_name=data.last_name,
        role=UserRole.STUDENT,
    )

    db.add(user)

    # nécessaire pour obtenir user.id
    db.flush()

    otp = create_email_verification_otp(user)

    record_audit_event(
        db,
        event_type=AuditEventType.USER_CREATED,
        entity_type="user",
        entity_id=user.id,
        action="register",
        new_values={"email": user.email, "role": user.role},
    )
    db.commit()
    db.refresh(user)

    try:
        send_verification_email(user.email, otp)
    except EmailDeliveryError:
        record_audit_event(
            db,
            event_type=AuditEventType.EMAIL_VERIFICATION_SEND_FAILED,
            entity_type="user",
            entity_id=user.id,
            action="register",
        )
        db.commit()
        raise EmailSendError() from None

    record_audit_event(
        db,
        event_type=AuditEventType.EMAIL_VERIFICATION_SENT,
        entity_type="user",
        entity_id=user.id,
        action="register",
    )
    db.commit()

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
        record_audit_event(
            db,
            event_type=AuditEventType.LOGIN_FAILED,
            action="login",
            metadata={"email": email},
        )
        db.commit()
        raise InvalidCredentialsError()

    if not verify_password(
        password,
        user.password_hash,
    ):
        record_audit_event(
            db,
            event_type=AuditEventType.LOGIN_FAILED,
            entity_type="user",
            entity_id=user.id,
            action="login",
            metadata={"email": user.email},
        )
        db.commit()
        raise InvalidCredentialsError()

    if not user.is_active:
        raise AccountDisabledError()

    if user.email_verified_at is None:
        raise EmailNotVerifiedError()

    user.last_login_at = datetime.now(UTC)
    record_audit_event(
        db,
        event_type=AuditEventType.USER_LOGIN,
        actor_user_id=user.id,
        entity_type="user",
        entity_id=user.id,
        action="login",
    )
    db.commit()
    db.refresh(user)

    return user


def create_user_by_admin(
    db: Session,
    data: AdminCreateUserRequest,
) -> User:

    email = normalize_email(str(data.email))

    existing_user = get_user_by_email(
        db,
        email,
    )

    if existing_user is not None:
        raise EmailAlreadyExistsError()

    user = User(
        email=email,
        password_hash=hash_password(data.password),
        first_name=data.first_name,
        last_name=data.last_name,
        role=data.role,
    )

    db.add(user)
    db.flush()

    otp = create_email_verification_otp(user)

    record_audit_event(
        db,
        event_type=AuditEventType.USER_CREATED,
        actor_user_id=None,
        entity_type="user",
        entity_id=user.id,
        action="admin_create",
        new_values={"email": user.email, "role": user.role},
    )
    db.commit()
    db.refresh(user)

    try:
        record_audit_event(
            db,
            event_type=AuditEventType.EMAIL_VERIFICATION_SENT,
            entity_type="user",
            entity_id=user.id,
            action="admin_create",
        )
        db.commit()
        send_verification_email(
            user.email,
            otp,
            user.first_name,
        )

    except EmailDeliveryError:
        record_audit_event(
            db,
            event_type=AuditEventType.EMAIL_VERIFICATION_SEND_FAILED,
            entity_type="user",
            entity_id=user.id,
            action="admin_create",
        )
        db.commit()
        raise EmailSendError()

    return user
