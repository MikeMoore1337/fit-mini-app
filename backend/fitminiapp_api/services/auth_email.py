from __future__ import annotations

import smtplib
import ssl
from email.message import EmailMessage
from urllib.parse import urlencode

from fitminiapp_api.core.config import settings


def send_auth_email(recipient: str, *, subject: str, body: str) -> bool:
    """Deliver one transactional auth email; return False in unconfigured dev/test."""

    if not settings.smtp_host.strip() or not settings.smtp_from_email.strip():
        return False

    message = EmailMessage()
    message["From"] = settings.smtp_from_email
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(body)

    smtp_class = smtplib.SMTP_SSL if settings.smtp_use_ssl else smtplib.SMTP
    with smtp_class(settings.smtp_host, settings.smtp_port, timeout=15) as client:
        if settings.smtp_starttls and not settings.smtp_use_ssl:
            client.starttls(context=ssl.create_default_context())
        if settings.smtp_username:
            client.login(settings.smtp_username, settings.smtp_password)
        client.send_message(message)
    return True


def verification_email(email: str, raw_token: str, *, next_path: str | None = None) -> bool:
    query = {"token": raw_token}
    if next_path:
        query["next"] = next_path
    url = f"{settings.frontend_base_url.rstrip('/')}/verify-email?{urlencode(query)}"
    return send_auth_email(
        email,
        subject="Подтвердите email — Your Fitness Coach",
        body=(
            "Подтвердите адрес электронной почты, чтобы войти в Your Fitness Coach.\n\n"
            f"{url}\n\nСсылка действует 24 часа."
        ),
    )


def password_reset_email(email: str, raw_token: str) -> bool:
    url = f"{settings.frontend_base_url.rstrip('/')}/reset-password?token={raw_token}"
    return send_auth_email(
        email,
        subject="Восстановление доступа — Your Fitness Coach",
        body=(
            "Для создания нового пароля перейдите по ссылке:\n\n"
            f"{url}\n\nСсылка действует 1 час. Если вы не запрашивали восстановление, "
            "ничего делать не нужно."
        ),
    )
