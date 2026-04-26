"""convert business timestamps to MSK

Revision ID: 0008_business_time_msk
Revises: 0007_add_nutrition_targets
Create Date: 2026-04-25
"""

from alembic import op

revision = "0008_business_time_msk"
down_revision = "0007_add_nutrition_targets"
branch_labels = None
depends_on = None


BUSINESS_TIMESTAMP_COLUMNS = [
    ("users", "created_at"),
    ("coach_clients", "created_at"),
    ("coach_client_invites", "created_at"),
    ("program_templates", "created_at"),
    ("user_programs", "assigned_at"),
    ("user_workouts", "started_at"),
    ("user_workouts", "completed_at"),
    ("notifications", "scheduled_for"),
    ("notifications", "created_at"),
    ("notifications", "sent_at"),
    ("nutrition_targets", "saved_at"),
    ("subscriptions", "starts_at"),
    ("subscriptions", "ends_at"),
    ("subscriptions", "created_at"),
    ("payments", "created_at"),
    ("payments", "paid_at"),
]


def _shift_timestamp(table_name: str, column_name: str, hours: int) -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "postgresql":
        direction = "+" if hours > 0 else "-"
        op.execute(
            f"""
            UPDATE {table_name}
            SET {column_name} = {column_name} {direction} INTERVAL '3 hours'
            WHERE {column_name} IS NOT NULL
            """
        )
        return

    if dialect == "sqlite":
        modifier = "+3 hours" if hours > 0 else "-3 hours"
        op.execute(
            f"""
            UPDATE {table_name}
            SET {column_name} = datetime({column_name}, '{modifier}')
            WHERE {column_name} IS NOT NULL
            """
        )
        return

    raise RuntimeError(f"Unsupported database dialect for MSK migration: {dialect}")


def upgrade() -> None:
    for table_name, column_name in BUSINESS_TIMESTAMP_COLUMNS:
        _shift_timestamp(table_name, column_name, hours=3)


def downgrade() -> None:
    for table_name, column_name in BUSINESS_TIMESTAMP_COLUMNS:
        _shift_timestamp(table_name, column_name, hours=-3)
