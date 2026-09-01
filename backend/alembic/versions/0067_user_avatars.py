"""Add private normalized user avatars.

Revision ID: 0067_user_avatars
Revises: 0066_workout_metric_backfill
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0067_user_avatars"
down_revision: str | None = "0066_workout_metric_backfill"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

online_rollout_phase = "expand"
online_rollout_notes = (
    "Eight nullable columns only; no default, constraint, index, existing-row rewrite or backfill."
)


def upgrade() -> None:
    op.add_column("users", sa.Column("custom_avatar_content_type", sa.String(32), nullable=True))
    op.add_column("users", sa.Column("custom_avatar_image_bytes", sa.LargeBinary(), nullable=True))
    op.add_column("users", sa.Column("custom_avatar_byte_size", sa.Integer(), nullable=True))
    op.add_column("users", sa.Column("custom_avatar_width", sa.Integer(), nullable=True))
    op.add_column("users", sa.Column("custom_avatar_height", sa.Integer(), nullable=True))
    op.add_column("users", sa.Column("custom_avatar_sha256", sa.String(64), nullable=True))
    op.add_column("users", sa.Column("custom_avatar_created_at", sa.DateTime(), nullable=True))
    op.add_column("users", sa.Column("custom_avatar_updated_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "custom_avatar_updated_at")
    op.drop_column("users", "custom_avatar_created_at")
    op.drop_column("users", "custom_avatar_sha256")
    op.drop_column("users", "custom_avatar_height")
    op.drop_column("users", "custom_avatar_width")
    op.drop_column("users", "custom_avatar_byte_size")
    op.drop_column("users", "custom_avatar_image_bytes")
    op.drop_column("users", "custom_avatar_content_type")
