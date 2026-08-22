from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from fitminiapp_api.db.base import Base


class BotSupportCase(Base):
    """Minimal routing metadata for a Telegram support request.

    The private request body and media remain in Telegram and are never persisted here.
    """

    __tablename__ = "bot_support_cases"
    __table_args__ = (
        UniqueConstraint(
            "telegram_user_id",
            "request_message_id",
            name="uq_bot_support_cases_user_message",
        ),
        CheckConstraint(
            "category IN ('bug', 'account', 'idea', 'contact', 'other')",
            name="ck_bot_support_cases_category",
        ),
        CheckConstraint(
            "status IN ('pending_relay', 'open', 'replying', 'replied', "
            "'relay_failed', 'undeliverable', 'expired')",
            name="ck_bot_support_cases_status",
        ),
        Index(
            "ix_bot_support_cases_rate_limit",
            "telegram_user_id",
            "category",
            "created_at",
        ),
        Index("ix_bot_support_cases_status_expires", "status", "expires_at"),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    telegram_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    request_message_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    category: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    reply_admin_telegram_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    reply_message_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    reply_claimed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    replied_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
