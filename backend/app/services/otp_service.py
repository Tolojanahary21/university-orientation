import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta

from app.core.config import (
    OTP_MAX_ATTEMPTS,
    OTP_RESEND_COOLDOWN_SECONDS,
    OTP_SECRET_KEY,
    OTP_TTL_MINUTES,
)
from app.models.user import User


class OTPError(Exception):
    pass


class OTPExpiredError(OTPError):
    pass


class OTPInvalidError(OTPError):
    pass


class OTPBlockedError(OTPError):
    pass


class OTPCooldownError(OTPError):
    def __init__(self, retry_after: int):
        self.retry_after = retry_after


def utc_now() -> datetime:
    return datetime.now(UTC)


def generate_otp() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def build_otp_hash(
    user: User,
    otp: str,
) -> str:
    payload = (f"email_verification:{user.id}:{otp}").encode()

    return hmac.new(
        OTP_SECRET_KEY.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()


def create_email_verification_otp(
    user: User,
) -> str:

    now = utc_now()

    if user.otp_last_sent_at is not None:
        elapsed = (now - user.otp_last_sent_at).total_seconds()

        if elapsed < OTP_RESEND_COOLDOWN_SECONDS:
            remaining = int(OTP_RESEND_COOLDOWN_SECONDS - elapsed)

            raise OTPCooldownError(max(1, remaining))

    otp = generate_otp()

    user.otp_hash = build_otp_hash(
        user,
        otp,
    )

    user.otp_expires_at = now + timedelta(minutes=OTP_TTL_MINUTES)

    user.otp_attempts = 0
    user.otp_last_sent_at = now

    return otp


def verify_email_otp(
    user: User,
    otp: str,
) -> None:

    if user.email_verified_at is not None:
        return

    now = utc_now()

    if user.otp_hash is None or user.otp_expires_at is None:
        raise OTPInvalidError()

    if now > user.otp_expires_at:
        user.otp_hash = None
        user.otp_expires_at = None

        raise OTPExpiredError()

    if user.otp_attempts >= OTP_MAX_ATTEMPTS:
        raise OTPBlockedError()

    incoming_hash = build_otp_hash(
        user,
        otp,
    )

    valid = hmac.compare_digest(
        incoming_hash,
        user.otp_hash,
    )

    if not valid:
        user.otp_attempts += 1

        if user.otp_attempts >= OTP_MAX_ATTEMPTS:
            user.otp_hash = None
            user.otp_expires_at = None

            raise OTPBlockedError()

        raise OTPInvalidError()

    user.email_verified_at = now

    user.otp_hash = None
    user.otp_expires_at = None
    user.otp_attempts = 0
