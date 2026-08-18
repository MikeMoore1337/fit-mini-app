"""add external authentication identities

Revision ID: 0029_auth_identities
Revises: 0028_schema_metadata_sync
Create Date: 2026-08-11
"""

import sqlalchemy as sa

from alembic import op

revision = "0029_auth_identities"
down_revision = "0028_schema_metadata_sync"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "auth_identities",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("subject", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("email_verified", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("last_login_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider", "subject", name="uq_auth_identities_provider_subject"),
        sa.UniqueConstraint("user_id", "provider", name="uq_auth_identities_user_provider"),
    )
    op.create_index("ix_auth_identities_provider", "auth_identities", ["provider"], unique=False)
    op.create_index("ix_auth_identities_user_id", "auth_identities", ["user_id"], unique=False)
    op.execute(
        sa.text(
            "INSERT INTO auth_identities "
            "(user_id, provider, subject, email_verified, created_at, last_login_at) "
            "SELECT id, 'telegram', CAST(telegram_user_id AS VARCHAR(255)), false, "
            "created_at, created_at FROM users"
        )
    )


def downgrade() -> None:
    op.drop_index("ix_auth_identities_user_id", table_name="auth_identities")
    op.drop_index("ix_auth_identities_provider", table_name="auth_identities")
    op.drop_table("auth_identities")
