"""Add short-lived account data export artifacts.

Revision ID: 0057_account_data_exports
Revises: 0056_notification_orchestration
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0057_account_data_exports"
down_revision: str | None = "0056_notification_orchestration"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "account_data_exports",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("export_id", sa.String(length=36), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("archive_bytes", sa.LargeBinary(), nullable=True),
        sa.Column("filename", sa.String(length=128), nullable=True),
        sa.Column("content_size_bytes", sa.Integer(), nullable=True),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("download_token_hash", sa.String(length=64), nullable=True),
        sa.Column("download_token_expires_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint(
            "content_size_bytes IS NULL OR content_size_bytes >= 0",
            name="ck_account_data_exports_content_size",
        ),
        sa.CheckConstraint(
            "status IN ('generating', 'ready', 'expired', 'error')",
            name="ck_account_data_exports_status",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("export_id", name="uq_account_data_exports_export_id"),
        sa.UniqueConstraint("user_id", name="uq_account_data_exports_user_id"),
    )
    op.create_index(
        "ix_account_data_exports_download_token_hash",
        "account_data_exports",
        ["download_token_hash"],
        unique=False,
    )
    op.create_index(
        "ix_account_data_exports_expires_at",
        "account_data_exports",
        ["expires_at"],
        unique=False,
    )
    op.create_index(
        "ix_account_data_exports_export_id",
        "account_data_exports",
        ["export_id"],
        unique=False,
    )
    op.create_index(
        "ix_account_data_exports_user_id",
        "account_data_exports",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_account_data_exports_user_id", table_name="account_data_exports")
    op.drop_index("ix_account_data_exports_export_id", table_name="account_data_exports")
    op.drop_index("ix_account_data_exports_expires_at", table_name="account_data_exports")
    op.drop_index("ix_account_data_exports_download_token_hash", table_name="account_data_exports")
    op.drop_table("account_data_exports")
