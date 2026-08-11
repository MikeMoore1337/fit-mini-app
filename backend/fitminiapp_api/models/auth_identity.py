from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from fitminiapp_api.core.timezone import now_msk_naive
from fitminiapp_api.db.base import Base


class AuthIdentity(Base):
    """One verified external identity attached to an internal user account."""

    __tablename__ = "auth_identities"
    __table_args__ = (
        UniqueConstraint("provider", "subject", name="uq_auth_identities_provider_subject"),
        UniqueConstraint("user_id", "provider", name="uq_auth_identities_user_provider"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    provider: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    email_verified: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=now_msk_naive)
    last_login_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=now_msk_naive)

    user = relationship("User", back_populates="auth_identities")


class LocalCredential(Base):
    __tablename__ = "local_credentials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    username_normalized: Mapped[str] = mapped_column(
        String(32), nullable=False, unique=True, index=True
    )
    password_hash: Mapped[str] = mapped_column(String(512), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=now_msk_naive)
    password_changed_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=now_msk_naive
    )


class AuthActionToken(Base):
    __tablename__ = "auth_action_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    purpose: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=now_msk_naive)
