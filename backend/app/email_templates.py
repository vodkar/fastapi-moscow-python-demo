"""Email template rendering and generation utilities."""

from dataclasses import dataclass
from pathlib import Path

from jinja2 import Template

from app.core.config import settings


@dataclass
class EmailData:
    """Data structure for email content and metadata."""

    html_content: str
    subject: str


def render_email_template(*, template_name: str, context: dict[str, str | int]) -> str:
    """Render email template with provided context."""
    template_str = (
        Path(__file__).parent / "email-templates" / "build" / template_name
    ).read_text()
    return Template(template_str).render(context)


def generate_test_email(email_to: str) -> EmailData:
    """Generate test email data."""
    project_name = settings.PROJECT_NAME
    subject = f"{project_name} - Test email"
    html_content = render_email_template(
        template_name="test_email.html",
        context={"project_name": settings.PROJECT_NAME, "email": email_to},
    )
    return EmailData(html_content=html_content, subject=subject)


def generate_reset_password_email(email_to: str, email: str, token: str) -> EmailData:
    """Generate password reset email data."""
    project_name = settings.PROJECT_NAME
    subject = f"{project_name} - Password recovery for user {email}"
    link = f"{settings.FRONTEND_HOST}/reset-password?token={token}"
    html_content = render_email_template(
        template_name="reset_password.html",
        context={
            "project_name": settings.PROJECT_NAME,
            "username": email,
            "email": email_to,
            "valid_hours": settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS,
            "link": link,
        },
    )
    return EmailData(html_content=html_content, subject=subject)


def generate_new_account_email(
    email_to: str,
    username: str,
    password: str,
) -> EmailData:
    """Generate new account confirmation email data."""
    project_name = settings.PROJECT_NAME
    subject = f"{project_name} - New account for user {username}"
    html_content = render_email_template(
        template_name="new_account.html",
        context={
            "project_name": settings.PROJECT_NAME,
            "username": username,
            "password": password,
            "email": email_to,
            "link": settings.FRONTEND_HOST,
        },
    )
    return EmailData(html_content=html_content, subject=subject)
