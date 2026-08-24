"""unify notification orchestration and preferences

Revision ID: 0056_notification_orchestration
Revises: 0055_nutrition_target_history
Create Date: 2026-08-24
"""

import sqlalchemy as sa

from alembic import op

revision = "0056_notification_orchestration"
down_revision = "0055_nutrition_target_history"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("notification_settings") as batch_op:
        batch_op.add_column(
            sa.Column(
                "measurement_reminders_enabled",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("false"),
            )
        )
        batch_op.add_column(
            sa.Column(
                "telegram_enabled",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("true"),
            )
        )
        batch_op.add_column(sa.Column("quiet_hours_start", sa.Time(), nullable=True))
        batch_op.add_column(sa.Column("quiet_hours_end", sa.Time(), nullable=True))
        batch_op.create_check_constraint(
            "ck_notification_settings_quiet_hours_pair",
            "(quiet_hours_start IS NULL AND quiet_hours_end IS NULL) OR "
            "(quiet_hours_start IS NOT NULL AND quiet_hours_end IS NOT NULL)",
        )

    with op.batch_alter_table("notifications") as batch_op:
        batch_op.add_column(
            sa.Column(
                "category",
                sa.String(length=48),
                nullable=False,
                server_default="custom_reminder",
            )
        )
        batch_op.add_column(
            sa.Column(
                "event_kind",
                sa.String(length=24),
                nullable=False,
                server_default="reminder",
            )
        )
        batch_op.add_column(sa.Column("read_at", sa.DateTime(), nullable=True))

    op.execute(
        """
        UPDATE notifications
        SET category = CASE
            WHEN dedupe_key LIKE 'workout:%' THEN 'workout_reminder'
            WHEN dedupe_key LIKE 'weekly_check_in:%' THEN 'weekly_check_in_reminder'
            WHEN dedupe_key LIKE 'trainer_feedback:%' THEN 'trainer_comment'
            WHEN dedupe_key LIKE 'trainer_request:%' THEN 'relationship_event'
            WHEN title LIKE '%программ%' OR title LIKE '%Программ%' THEN 'trainer_program_update'
            WHEN title LIKE '%КБЖУ%' OR title LIKE '%питан%' THEN 'nutrition_update'
            ELSE 'custom_reminder'
        END
        """
    )
    op.execute(
        """
        UPDATE notifications
        SET event_kind = CASE
            WHEN category IN (
                'workout_reminder',
                'weekly_check_in_reminder',
                'measurement_reminder',
                'custom_reminder'
            ) THEN 'reminder'
            ELSE 'transactional'
        END
        """
    )

    with op.batch_alter_table("notifications") as batch_op:
        batch_op.create_check_constraint(
            "ck_notifications_event_kind",
            "event_kind IN ('reminder', 'transactional', 'security')",
        )
        batch_op.create_index("ix_notifications_read_at", ["read_at"])


def downgrade() -> None:
    with op.batch_alter_table("notifications") as batch_op:
        batch_op.drop_index("ix_notifications_read_at")
        batch_op.drop_constraint("ck_notifications_event_kind", type_="check")
        batch_op.drop_column("read_at")
        batch_op.drop_column("event_kind")
        batch_op.drop_column("category")

    with op.batch_alter_table("notification_settings") as batch_op:
        batch_op.drop_constraint("ck_notification_settings_quiet_hours_pair", type_="check")
        batch_op.drop_column("quiet_hours_end")
        batch_op.drop_column("quiet_hours_start")
        batch_op.drop_column("telegram_enabled")
        batch_op.drop_column("measurement_reminders_enabled")
