"""preserve workout history and harden queue integrity

Revision ID: 0014_hardening_data_integrity
Revises: 0013_notification_delivery_state
Create Date: 2026-07-20
"""

from datetime import UTC, datetime
from zoneinfo import ZoneInfo

import sqlalchemy as sa

from alembic import op

revision = "0014_hardening_data_integrity"
down_revision = "0013_notification_delivery_state"
branch_labels = None
depends_on = None

DEFAULT_TIMEZONE = "Europe/Moscow"


def _as_datetime(value: datetime | str) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(value)


def _backfill_notification_utc() -> None:
    connection = op.get_bind()
    rows = connection.execute(
        sa.text(
            """
            SELECT n.id, n.scheduled_for, COALESCE(p.timezone, :default_timezone) AS timezone
            FROM notifications AS n
            LEFT JOIN user_profiles AS p ON p.user_id = n.user_id
            WHERE n.scheduled_for_utc IS NULL
            """
        ),
        {"default_timezone": DEFAULT_TIMEZONE},
    ).mappings()

    for row in rows:
        try:
            timezone = ZoneInfo(row["timezone"] or DEFAULT_TIMEZONE)
        except Exception:
            timezone = ZoneInfo(DEFAULT_TIMEZONE)
        local_value = _as_datetime(row["scheduled_for"])
        if local_value.tzinfo is None:
            local_value = local_value.replace(tzinfo=timezone)
        utc_value = local_value.astimezone(UTC).replace(tzinfo=None)
        connection.execute(
            sa.text(
                "UPDATE notifications SET scheduled_for_utc = :scheduled_for_utc WHERE id = :id"
            ),
            {"scheduled_for_utc": utc_value, "id": row["id"]},
        )


def upgrade() -> None:
    op.alter_column("user_programs", "template_id", existing_type=sa.Integer(), nullable=True)

    # Если старые параллельные назначения создали несколько активных программ,
    # сохраняем активной только последнюю, не удаляя историю остальных.
    op.execute(
        """
        UPDATE user_programs
        SET is_active = false
        WHERE is_active = true
          AND id NOT IN (
              SELECT MAX(id) FROM user_programs WHERE is_active = true GROUP BY user_id
          )
        """
    )
    op.create_index(
        "uq_user_programs_one_active_per_user",
        "user_programs",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("is_active"),
        sqlite_where=sa.text("is_active = 1"),
    )
    # Номер подхода уникален внутри упражнения. Если до ограничения в БД
    # успели появиться дубли, сохраняем последнюю запись как наиболее свежую.
    op.execute(
        """
        DELETE FROM user_workout_sets
        WHERE id NOT IN (
            SELECT MAX(id)
            FROM user_workout_sets
            GROUP BY workout_exercise_id, set_number
        )
        """
    )
    op.create_unique_constraint(
        "uq_user_workout_sets_exercise_number",
        "user_workout_sets",
        ["workout_exercise_id", "set_number"],
    )

    op.add_column("notifications", sa.Column("scheduled_for_utc", sa.DateTime(), nullable=True))
    _backfill_notification_utc()
    op.alter_column(
        "notifications",
        "scheduled_for_utc",
        existing_type=sa.DateTime(),
        nullable=False,
    )
    op.create_index(
        "ix_notifications_scheduled_for_utc",
        "notifications",
        ["scheduled_for_utc"],
    )


def downgrade() -> None:
    op.drop_index("ix_notifications_scheduled_for_utc", table_name="notifications")
    op.drop_column("notifications", "scheduled_for_utc")
    op.drop_constraint(
        "uq_user_workout_sets_exercise_number",
        "user_workout_sets",
        type_="unique",
    )
    op.drop_index("uq_user_programs_one_active_per_user", table_name="user_programs")
    op.alter_column("user_programs", "template_id", existing_type=sa.Integer(), nullable=False)
