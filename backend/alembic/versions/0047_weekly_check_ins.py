"""add weekly check-in history

Revision ID: 0047_weekly_check_ins
Revises: 0046_energy_calibrations
Create Date: 2026-08-19
"""

import sqlalchemy as sa

from alembic import op

revision = "0047_weekly_check_ins"
down_revision = "0046_energy_calibrations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "weekly_check_ins",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("week_start", sa.Date(), nullable=False),
        sa.Column("week_end", sa.Date(), nullable=False),
        sa.Column("submitted_on", sa.Date(), nullable=False),
        sa.Column("timezone", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("summary_version", sa.String(length=32), nullable=False),
        sa.Column("summary", sa.JSON(), nullable=False),
        sa.Column("training_load", sa.Integer(), nullable=True),
        sa.Column("recovery", sa.Integer(), nullable=True),
        sa.Column("hunger", sa.Integer(), nullable=True),
        sa.Column("adherence_difficulty", sa.Integer(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "status IN ('completed', 'skipped')",
            name="ck_weekly_check_ins_status",
        ),
        sa.CheckConstraint(
            "training_load IS NULL OR training_load BETWEEN 1 AND 5",
            name="ck_weekly_check_ins_training_load",
        ),
        sa.CheckConstraint(
            "recovery IS NULL OR recovery BETWEEN 1 AND 5",
            name="ck_weekly_check_ins_recovery",
        ),
        sa.CheckConstraint(
            "hunger IS NULL OR hunger BETWEEN 1 AND 5",
            name="ck_weekly_check_ins_hunger",
        ),
        sa.CheckConstraint(
            "adherence_difficulty IS NULL OR adherence_difficulty BETWEEN 1 AND 5",
            name="ck_weekly_check_ins_adherence_difficulty",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "week_start", name="uq_weekly_check_ins_user_week"),
    )
    op.create_index(
        "ix_weekly_check_ins_user_created",
        "weekly_check_ins",
        ["user_id", "created_at", "id"],
    )

    with op.batch_alter_table("notification_settings") as batch_op:
        batch_op.add_column(
            sa.Column(
                "weekly_check_in_reminders_enabled",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("true"),
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("notification_settings") as batch_op:
        batch_op.drop_column("weekly_check_in_reminders_enabled")
    op.drop_index("ix_weekly_check_ins_user_created", table_name="weekly_check_ins")
    op.drop_table("weekly_check_ins")
