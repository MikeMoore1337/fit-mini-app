"""add append-only application audit events

Revision ID: 0024_audit_events
Revises: 0023_program_lifecycle
Create Date: 2026-08-02
"""

import sqlalchemy as sa

from alembic import op

revision = "0024_audit_events"
down_revision = "0023_program_lifecycle"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "audit_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("target_user_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("resource_type", sa.String(length=64), nullable=False),
        sa.Column("resource_id", sa.String(length=64), nullable=True),
        sa.Column("details", sa.JSON(), server_default=sa.text("'{}'"), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["target_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_events_actor_user_id", "audit_events", ["actor_user_id"])
    op.create_index("ix_audit_events_target_user_id", "audit_events", ["target_user_id"])
    op.create_index(
        "ix_audit_events_actor_created", "audit_events", ["actor_user_id", "created_at"]
    )
    op.create_index(
        "ix_audit_events_target_created", "audit_events", ["target_user_id", "created_at"]
    )
    op.create_index("ix_audit_events_action_created", "audit_events", ["action", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_audit_events_action_created", table_name="audit_events")
    op.drop_index("ix_audit_events_target_created", table_name="audit_events")
    op.drop_index("ix_audit_events_actor_created", table_name="audit_events")
    op.drop_index("ix_audit_events_target_user_id", table_name="audit_events")
    op.drop_index("ix_audit_events_actor_user_id", table_name="audit_events")
    op.drop_table("audit_events")
