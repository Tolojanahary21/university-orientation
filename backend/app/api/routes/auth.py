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
from app.core.audit_events import AuditEventType
from app.repositories.user_repository import (
    get_user_by_email,
)
from app.schemas.auth import (
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    ResendOTPRequest,
    TokenResponse,
    VerifyEmailRequest,
)
from app.schemas.user import UserResponse
from app.services.audit_event_service import record_audit_event
from app.services.auth_service import (
    AccountDisabledError,
    EmailAlreadyExistsError,
    EmailNotVerifiedError,
    EmailSendError,
    InvalidCredentialsError,
    authenticate_user,
    register_user,
)
from app.services.email_service import (
    EmailDeliveryError,
    send_verification_email,
)
from app.services.otp_service import (
    OTPBlockedError,
    OTPCooldownError,
    OTPExpiredError,
    OTPInvalidError,
    create_email_verification_otp,
    verify_email_otp,
)
from app.services.token_service import (
    create_access_token,
)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    data: RegisterRequest,
    db: Session = Depends(get_db),
):
    try:
        return register_user(
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
                "Compte créé, mais l'e-mail de "
                "vérification n'a pas pu être envoyé. "
                "Utilisez resend-otp."
            ),
        )


@router.post(
    "/verify-email",
    response_model=MessageResponse,
)
def verify_email(
    data: VerifyEmailRequest,
    db: Session = Depends(get_db),
):
    user = get_user_by_email(
        db,
        str(data.email),
        for_update=True,
    )

    if user is None:
        raise HTTPException(
            status_code=400,
            detail="Code invalide.",
        )

    try:
        was_verified = user.email_verified_at is not None
        verify_email_otp(
            user,
            data.otp,
        )
        if not was_verified:
            record_audit_event(
                db,
                event_type=AuditEventType.EMAIL_VERIFIED,
                entity_type="user",
                entity_id=user.id,
                action="verify_email",
            )
        db.commit()

    except OTPExpiredError:
        record_audit_event(
            db,
            event_type=AuditEventType.EMAIL_VERIFICATION_FAILED,
            entity_type="user",
            entity_id=user.id,
            action="verify_email",
            metadata={"reason": "expired"},
        )
        db.commit()

        raise HTTPException(
            status_code=400,
            detail="Le code a expiré.",
        )

    except OTPInvalidError:
        record_audit_event(
            db,
            event_type=AuditEventType.EMAIL_VERIFICATION_FAILED,
            entity_type="user",
            entity_id=user.id,
            action="verify_email",
            metadata={"reason": "invalid"},
        )
        db.commit()

        raise HTTPException(
            status_code=400,
            detail="Code invalide.",
        )

    except OTPBlockedError:
        record_audit_event(
            db,
            event_type=AuditEventType.EMAIL_VERIFICATION_FAILED,
            entity_type="user",
            entity_id=user.id,
            action="verify_email",
            metadata={"reason": "blocked"},
        )
        db.commit()

        raise HTTPException(
            status_code=429,
            detail=("Trop de tentatives. Demandez un nouveau code."),
        )

    return {"message": "Adresse e-mail vérifiée."}


@router.post(
    "/resend-otp",
    response_model=MessageResponse,
)
def resend_otp(
    data: ResendOTPRequest,
    db: Session = Depends(get_db),
):
    user = get_user_by_email(
        db,
        str(data.email),
        for_update=True,
    )

    # réponse volontairement générique
    if user is None:
        return {"message": ("Si ce compte existe, un code sera envoyé.")}

    if user.email_verified_at is not None:
        return {
            "message": ("Si ce compte nécessite une vérification, un code sera envoyé.")
        }

    try:
        otp = create_email_verification_otp(user)

        record_audit_event(
            db,
            event_type=AuditEventType.EMAIL_VERIFICATION_SENT,
            entity_type="user",
            entity_id=user.id,
            action="resend_otp",
        )
        db.commit()

        send_verification_email(
            user.email,
            otp,
        )

    except OTPCooldownError as exc:
        db.rollback()

        raise HTTPException(
            status_code=429,
            detail=(
                f"Attendez {exc.retry_after} secondes "
                "avant de demander un nouveau code."
            ),
        )

    except EmailDeliveryError:
        record_audit_event(
            db,
            event_type=AuditEventType.EMAIL_VERIFICATION_SEND_FAILED,
            entity_type="user",
            entity_id=user.id,
            action="resend_otp",
        )
        db.commit()
        raise HTTPException(
            status_code=503,
            detail="Impossible d'envoyer l'e-mail.",
        )

    return {"message": ("Si ce compte existe, un code sera envoyé.")}


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    data: LoginRequest,
    db: Session = Depends(get_db),
):
    try:
        user = authenticate_user(
            db,
            str(data.email),
            data.password,
        )

    except InvalidCredentialsError:
        raise HTTPException(
            status_code=401,
            detail="E-mail ou mot de passe incorrect.",
        )

    except EmailNotVerifiedError:
        raise HTTPException(
            status_code=403,
            detail="Adresse e-mail non vérifiée.",
        )

    except AccountDisabledError:
        raise HTTPException(
            status_code=403,
            detail="Compte désactivé.",
        )

    token = create_access_token(user.id)

    return {
        "access_token": token,
        "token_type": "bearer",
    }


@router.get(
    "/me",
    response_model=UserResponse,
)
def me(
    current_user=Depends(get_current_user),
):
    return current_user
