from datetime import UTC, datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from fitminiapp_api.db.base import Base


def utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class OAuthTransaction(Base):
    """Short-lived server-side state for one browser OAuth attempt."""

    __tablename__ = "oauth_transactions"
    __table_args__ = (
        CheckConstraint(
            "purpose IN ('login', 'link')",
            name="ck_oauth_transactions_purpose",
        ),
        CheckConstraint(
            "status IN ('pending', 'processing', 'completed', 'failed', 'expired')",
            name="ck_oauth_transactions_status",
        ),
        Index(
            "ix_oauth_transactions_browser_provider",
            "browser_marker_hash",
            "provider",
            "purpose",
        ),
        Index(
            "ix_oauth_transactions_expiry_status",
            "expires_at",
            "status",
        ),
    )

    transaction_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    browser_marker_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    purpose: Mapped[str] = mapped_column(String(16), nullable=False)
    state: Mapped[str] = mapped_column(String(256), nullable=False, unique=True, index=True)
    redirect_uri: Mapped[str] = mapped_column(String(512), nullable=False)
    next_path: Mapped[str | None] = mapped_column(String(256), nullable=True)
    code_verifier: Mapped[str | None] = mapped_column(String(256), nullable=True)
    nonce: Mapped[str | None] = mapped_column(String(256), nullable=True)
    link_action_token_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    link_user_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    session_family_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    claimed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(String(32), nullable=True)
