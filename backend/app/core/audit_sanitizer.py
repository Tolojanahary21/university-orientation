from collections.abc import Mapping

SENSITIVE_KEYS = frozenset(
    {
        "password",
        "password_hash",
        "otp",
        "otp_hash",
        "token",
        "access_token",
        "refresh_token",
        "authorization",
        "smtp_app_password",
        "jwt_secret_key",
        "otp_secret_key",
        "secret",
        "secret_key",
    }
)


def sanitize_audit_value(value):
    """Copy JSON-like data while recursively dropping credential fields."""
    if isinstance(value, str):
        import re

        value = re.sub(
            r"(?i)\bBearer\s+[A-Za-z0-9._~+/-]+=*",
            "[REDACTED]",
            value,
        )
        value = re.sub(
            r"\beyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b",
            "[REDACTED]",
            value,
        )
        return value
    if isinstance(value, Mapping):
        sanitized = {}
        for key, item in value.items():
            normalized_key = str(key).lower()
            if normalized_key == "authorization":
                sanitized[key] = "[REDACTED]"
            elif normalized_key not in SENSITIVE_KEYS:
                sanitized[key] = sanitize_audit_value(item)
        return sanitized
    if isinstance(value, (list, tuple)):
        return [sanitize_audit_value(item) for item in value]
    return value
