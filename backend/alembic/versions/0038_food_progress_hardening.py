"""harden food search and trainer progress queries

Revision ID: 0038_food_progress_hardening
Revises: 0037_recipes_copying
Create Date: 2026-08-18
"""

import sqlalchemy as sa

from alembic import op

revision = "0038_food_progress_hardening"
down_revision = "0037_recipes_copying"
branch_labels = None
depends_on = None


def _normalize_search_text(name: str, brand: str | None) -> str:
    return " ".join(part for part in (name, brand or "") if part).casefold()


def _backfill_search_text() -> None:
    connection = op.get_bind()
    last_id = 0
    while True:
        rows = (
            connection.execute(
                sa.text(
                    """
                    SELECT id, name, brand
                    FROM foods
                    WHERE id > :last_id
                    ORDER BY id
                    LIMIT 1000
                    """
                ),
                {"last_id": last_id},
            )
            .mappings()
            .all()
        )
        if not rows:
            return
        connection.execute(
            sa.text("UPDATE foods SET search_text = :search_text WHERE id = :id"),
            [
                {
                    "id": row["id"],
                    "search_text": _normalize_search_text(row["name"], row["brand"]),
                }
                for row in rows
            ],
        )
        last_id = rows[-1]["id"]


def upgrade() -> None:
    bind = op.get_bind()
    _backfill_search_text()
    if bind.dialect.name == "postgresql":
        op.execute(sa.text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
        op.create_index(
            "ix_foods_search_text_trgm",
            "foods",
            ["search_text"],
            postgresql_using="gin",
            postgresql_ops={"search_text": "gin_trgm_ops"},
        )
    else:
        op.create_index("ix_foods_search_text_trgm", "foods", ["search_text"])

    op.drop_index("ix_coach_clients_coach_status", table_name="coach_clients")
    op.create_index(
        "ix_coach_clients_coach_status_client",
        "coach_clients",
        ["coach_user_id", "status", "client_user_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_coach_clients_coach_status_client",
        table_name="coach_clients",
    )
    op.create_index(
        "ix_coach_clients_coach_status",
        "coach_clients",
        ["coach_user_id", "status"],
    )
    op.drop_index("ix_foods_search_text_trgm", table_name="foods")
