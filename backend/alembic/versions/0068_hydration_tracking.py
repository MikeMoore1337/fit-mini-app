"""Add hydration goals, entries, presets, and optional profile sex.

Revision ID: 0068_hydration_tracking
Revises: 0067_user_avatars
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0068_hydration_tracking"
down_revision: str | None = "0067_user_avatars"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

online_rollout_phase = "expand"
online_rollout_notes = (
    "Adds one nullable profile column plus new empty hydration tables and indexes only those "
    "empty tables; metadata locks are bounded and existing rows are not rewritten."
)


def upgrade() -> None:
    op.add_column("user_profiles", sa.Column("sex", sa.String(16), nullable=True))
    op.create_table(
        "hydration_goals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("target_ml", sa.Integer(), nullable=True),
        sa.Column("source", sa.String(48), nullable=False),
        sa.Column("method_version", sa.String(64), nullable=False),
        sa.Column("reference_scope", sa.String(24), nullable=False, server_default="beverages"),
        sa.Column("sex", sa.String(16), nullable=True),
        sa.Column("adult_confirmed", sa.Boolean(), nullable=True),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("superseded_by_id", sa.Integer(), sa.ForeignKey("hydration_goals.id", ondelete="SET NULL"), nullable=True),
        sa.Column("request_key", sa.String(128), nullable=True),
        sa.Column("payload_fingerprint", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("status IN ('enabled', 'disabled')", name="ck_hydration_goals_status"),
        sa.CheckConstraint("source IN ('national_academies_beverages', 'manual')", name="ck_hydration_goals_source"),
        sa.CheckConstraint("(status = 'disabled' AND target_ml IS NULL) OR (status = 'enabled' AND target_ml BETWEEN 250 AND 10000)", name="ck_hydration_goals_target"),
        sa.CheckConstraint("effective_to IS NULL OR effective_to >= effective_from", name="ck_hydration_goals_effective_period"),
        sa.UniqueConstraint("user_id", "request_key", name="uq_hydration_goals_request_key"),
    )
    op.create_index("ix_hydration_goals_user_id", "hydration_goals", ["user_id"])
    op.create_index("ix_hydration_goals_user_effective", "hydration_goals", ["user_id", "effective_from"])
    op.create_index(
        "uq_hydration_goals_active_user",
        "hydration_goals",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("effective_to IS NULL"),
        sqlite_where=sa.text("effective_to IS NULL"),
    )
    op.create_table(
        "hydration_entries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("diary_date", sa.Date(), nullable=False),
        sa.Column("timezone", sa.String(64), nullable=False),
        sa.Column("volume_ml", sa.Integer(), nullable=False),
        sa.Column("beverage_type", sa.String(16), nullable=False),
        sa.Column("source", sa.String(16), nullable=False),
        sa.Column("request_key", sa.String(128), nullable=False),
        sa.Column("payload_fingerprint", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("volume_ml BETWEEN 1 AND 5000", name="ck_hydration_entries_volume"),
        sa.CheckConstraint("beverage_type IN ('water', 'tea', 'coffee', 'milk', 'juice', 'other')", name="ck_hydration_entries_beverage_type"),
        sa.CheckConstraint("source IN ('quick_preset', 'manual', 'history_edit')", name="ck_hydration_entries_source"),
        sa.UniqueConstraint("user_id", "request_key", name="uq_hydration_entries_request_key"),
    )
    op.create_index("ix_hydration_entries_user_id", "hydration_entries", ["user_id"])
    op.create_index("ix_hydration_entries_user_day", "hydration_entries", ["user_id", "diary_date", "occurred_at"])
    op.create_table(
        "hydration_presets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("label", sa.String(40), nullable=False),
        sa.Column("volume_ml", sa.Integer(), nullable=False),
        sa.Column("beverage_type", sa.String(16), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("volume_ml BETWEEN 1 AND 5000", name="ck_hydration_presets_volume"),
        sa.CheckConstraint("beverage_type IN ('water', 'tea', 'coffee', 'milk', 'juice', 'other')", name="ck_hydration_presets_beverage_type"),
        sa.CheckConstraint("length(label) BETWEEN 1 AND 40", name="ck_hydration_presets_label"),
        sa.UniqueConstraint("user_id", "label", name="uq_hydration_presets_user_label"),
    )
    op.create_index("ix_hydration_presets_user_id", "hydration_presets", ["user_id"])


def downgrade() -> None:
    op.drop_table("hydration_presets")
    op.drop_table("hydration_entries")
    op.drop_table("hydration_goals")
    op.drop_column("user_profiles", "sex")
