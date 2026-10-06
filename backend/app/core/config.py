import os

from dotenv import load_dotenv

load_dotenv()


def require_env(name: str) -> str:
    value = os.getenv(name)

    if not value:
        raise RuntimeError(f"La variable d'environnement {name} est obligatoire.")

    return value


DATABASE_URL = require_env("DATABASE_URL")

JWT_SECRET_KEY = require_env("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ACCESS_TOKEN_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_MINUTES", "60"))

OTP_SECRET_KEY = require_env("OTP_SECRET_KEY")
OTP_TTL_MINUTES = int(os.getenv("OTP_TTL_MINUTES", "10"))
OTP_MAX_ATTEMPTS = int(os.getenv("OTP_MAX_ATTEMPTS", "5"))
OTP_RESEND_COOLDOWN_SECONDS = int(os.getenv("OTP_RESEND_COOLDOWN_SECONDS", "60"))

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = require_env("SMTP_USERNAME")
SMTP_APP_PASSWORD = require_env("SMTP_APP_PASSWORD")
SMTP_FROM_EMAIL = require_env("SMTP_FROM_EMAIL")
SMTP_FROM_NAME = os.getenv(
    "SMTP_FROM_NAME",
    "Orientation Universitaire",
)
