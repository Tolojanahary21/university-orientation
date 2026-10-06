import smtplib
import ssl
from email.message import EmailMessage

from app.core.config import (
    OTP_TTL_MINUTES,
    SMTP_APP_PASSWORD,
    SMTP_FROM_EMAIL,
    SMTP_FROM_NAME,
    SMTP_HOST,
    SMTP_PORT,
    SMTP_USERNAME,
)


class EmailDeliveryError(Exception):
    pass


def send_verification_email(
    email: str,
    otp: str,
    first_name: str | None = None,
) -> None:
    display_name = first_name.strip() if first_name else "Cher utilisateur"

    message = EmailMessage()
    message["Subject"] = "Vérification de votre compte"
    message["From"] = f"{SMTP_FROM_NAME} <{SMTP_FROM_EMAIL}>"
    message["To"] = email

    # Version texte brut (fallback)
    message.set_content(
        f"""
Bonjour {display_name},

Bienvenue sur {SMTP_FROM_NAME}.

Utilisez le code suivant pour vérifier votre adresse e-mail :

{otp}

Ce code est valable pendant {OTP_TTL_MINUTES} minutes.

Ne partagez jamais ce code avec qui que ce soit.

Si vous n'êtes pas à l'origine de cette demande,
vous pouvez simplement ignorer cet e-mail.

Cordialement,
{SMTP_FROM_NAME}
""".strip()
    )

    # Version HTML
    message.add_alternative(
        f"""
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Vérification de votre compte</title>
</head>
<body style="margin:0; padding:0; background-color:#f4f7fb; font-family:Arial, Helvetica, sans-serif; color:#1f2937;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color:#f4f7fb; margin:0; padding:30px 15px;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:600px; background-color:#ffffff; border-radius:16px; overflow:hidden; box-shadow:0 6px 18px rgba(0,0,0,0.08);">
          
          <!-- Header -->
          <tr>
            <td style="background:linear-gradient(135deg, #2563eb, #1d4ed8); padding:32px 24px; text-align:center;">
              <div style="font-size:34px; line-height:1;">🎓</div>
              <div style="margin-top:10px; font-size:28px; font-weight:700; color:#ffffff; letter-spacing:1px;">
                ORIENTA
              </div>
              <div style="margin-top:6px; font-size:14px; color:#dbeafe;">
                Orientation Universitaire
              </div>
            </td>
          </tr>

          <!-- Body -->
          <tr>
            <td style="padding:36px 28px;">
              <h1 style="margin:0 0 18px 0; font-size:24px; color:#111827; text-align:center;">
                Vérifiez votre e-mail
              </h1>

              <p style="margin:0 0 16px 0; font-size:16px; line-height:1.6;">
                Bonjour <strong>{display_name}</strong>,
              </p>

              <p style="margin:0 0 22px 0; font-size:16px; line-height:1.6; color:#374151;">
                Merci de vous être inscrit sur <strong>{SMTP_FROM_NAME}</strong>.
                Utilisez le code ci-dessous pour confirmer votre adresse e-mail.
              </p>

              <div style="text-align:center; margin:28px 0;">
                <div style="display:inline-block; background-color:#eff6ff; border:2px dashed #93c5fd; border-radius:14px; padding:18px 30px;">
                  <span style="font-size:34px; font-weight:700; letter-spacing:10px; color:#1d4ed8;">
                    {otp}
                  </span>
                </div>
              </div>

              <p style="margin:0 0 10px 0; text-align:center; font-size:14px; color:#6b7280;">
                Ce code est valable pendant <strong>{OTP_TTL_MINUTES} minutes</strong>.
              </p>

              <div style="margin:26px 0 0 0; background-color:#fff7ed; border-left:4px solid #f59e0b; padding:14px 16px; border-radius:8px;">
                <p style="margin:0; font-size:14px; line-height:1.6; color:#92400e;">
                  <strong>Important :</strong> Ne partagez jamais ce code avec une autre personne.
                </p>
              </div>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="padding:22px 28px; background-color:#f9fafb; border-top:1px solid #e5e7eb;">
              <p style="margin:0 0 10px 0; font-size:13px; line-height:1.6; color:#6b7280;">
                Si vous n'êtes pas à l'origine de cette demande, vous pouvez simplement ignorer cet e-mail.
              </p>
              <p style="margin:0; font-size:12px; color:#9ca3af; text-align:center;">
                © 2026 ORIENTA — Orientation Universitaire
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>
        """,
        subtype="html",
    )

    context = ssl.create_default_context()

    try:
        with smtplib.SMTP(
            SMTP_HOST,
            SMTP_PORT,
            timeout=15,
        ) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()

            server.login(
                SMTP_USERNAME,
                SMTP_APP_PASSWORD,
            )

            server.send_message(message)

    except (smtplib.SMTPException, OSError) as exc:
        raise EmailDeliveryError() from exc