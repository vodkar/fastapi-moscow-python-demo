"""Utility functions for email sending and authentication tokens."""

import logging
from datetime import UTC, datetime, timedelta

import jwt
from emails import Message  # type: ignore[attr-defined]
from jwt.exceptions import InvalidTokenError

from app.core import security
from app.core.config import settings
from app.email_templates import (
    EmailData,
    generate_new_account_email,
    generate_reset_password_email,
    generate_test_email,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def send_email(
    *,
    email_to: str,
    subject: str = "",
    html_content: str = "",
) -> None:
    """Send email to specified recipient."""
    if not settings.emails_enabled:
        msg = "no provided configuration for email variables"
        raise ValueError(msg)
    message = Message(  # type: ignore[no-untyped-call]
        subject=subject,
        html=html_content,
        mail_from=(settings.EMAILS_FROM_NAME, settings.EMAILS_FROM_EMAIL),
    )
    smtp_options = {"host": settings.SMTP_HOST, "port": settings.SMTP_PORT}
    if settings.SMTP_TLS:
        smtp_options["tls"] = True
    elif settings.SMTP_SSL:
        smtp_options["ssl"] = True
    if settings.SMTP_USER:
        smtp_options["user"] = settings.SMTP_USER
    if settings.SMTP_PASSWORD:
        smtp_options["password"] = settings.SMTP_PASSWORD
    response = message.send(to=email_to, smtp=smtp_options)  # type: ignore[no-untyped-call]
    logger.info("send email result: %s", response)


def generate_password_reset_token(email: str) -> str:
    """Generate JWT token for password reset."""
    delta = timedelta(hours=settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS)
    now = datetime.now(UTC)
    expires = now + delta
    exp = expires.timestamp()
    return jwt.encode(
        {"exp": exp, "nbf": now, "sub": email},
        settings.SECRET_KEY,
        algorithm=security.ALGORITHM,
    )


def verify_password_reset_token(token: str) -> str | None:
    """Verify and decode password reset JWT token."""
    try:
        decoded_token = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[security.ALGORITHM],
        )
    except InvalidTokenError:
        return None
    return str(decoded_token["sub"])


__all__ = [
    "EmailData",
    "generate_new_account_email",
    "generate_password_reset_token",
    "generate_reset_password_email",
    "generate_test_email",
    "send_email",
    "verify_password_reset_token",
]
