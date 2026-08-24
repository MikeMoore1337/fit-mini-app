from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from fitminiapp_api.core.timezone import now_msk_naive
from fitminiapp_api.db.base import Base


class AccountDataExport(Base):
    """The single short-lived portability artifact owned by an account."""

    __tablename__ = "account_data_exports"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_account_data_exports_user_id"),
        UniqueConstraint("export_id", name="uq_account_data_exports_export_id"),
        CheckConstraint(
            "status IN ('generating', 'ready', 'expired', 'error')",
            name="ck_account_data_exports_status",
        ),
        CheckConstraint(
            "content_size_bytes IS NULL OR content_size_bytes >= 0",
            name="ck_account_data_exports_content_size",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    export_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    archive_bytes: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    filename: Mapped[str | None] = mapped_column(String(128), nullable=True)
    content_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    download_token_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    download_token_expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=now_msk_naive)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
