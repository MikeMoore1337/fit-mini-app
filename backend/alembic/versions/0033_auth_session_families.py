"""bind auth actions and refresh rotation to session families

Revision ID: 0033_auth_session_families
Revises: 0032_coach_role_applications
Create Date: 2026-08-18
"""

import sqlalchemy as sa

from alembic import op

revision = "0033_auth_session_families"
down_revision = "0032_coach_role_applications"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("refresh_tokens", sa.Column("family_id", sa.String(length=64), nullable=True))
    op.execute(sa.text("UPDATE refresh_tokens SET family_id = jti WHERE family_id IS NULL"))
    with op.batch_alter_table("refresh_tokens") as batch_op:
        batch_op.alter_column(
            "family_id",
            existing_type=sa.String(length=64),
            nullable=False,
        )
    op.create_index("ix_refresh_tokens_family_id", "refresh_tokens", ["family_id"], unique=False)

    op.add_column(
        "auth_action_tokens",
        sa.Column("session_family_id", sa.String(length=64), nullable=True),
    )
    op.create_index(
        "ix_auth_action_tokens_session_family_id",
        "auth_action_tokens",
        ["session_family_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_auth_action_tokens_session_family_id", table_name="auth_action_tokens")
    op.drop_column("auth_action_tokens", "session_family_id")
    op.drop_index("ix_refresh_tokens_family_id", table_name="refresh_tokens")
    op.drop_column("refresh_tokens", "family_id")
