"""add offline-safe workout set mutations

Revision ID: 0049_offline_workout_sync
Revises: 0048_workout_adaptations
Create Date: 2026-08-19
"""

import sqlalchemy as sa

from alembic import op

revision = "0049_offline_workout_sync"
down_revision = "0048_workout_adaptations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("user_workout_sets") as batch_op:
        batch_op.add_column(
            sa.Column("version", sa.Integer(), server_default="1", nullable=False)
        )
        batch_op.create_check_constraint(
            "ck_user_workout_sets_version_positive",
            "version >= 1",
        )

    op.create_table(
        "workout_set_mutations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("workout_set_id", sa.Integer(), nullable=False),
        sa.Column("mutation_id", sa.String(length=64), nullable=False),
        sa.Column("request_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("applied_version", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "applied_version >= 1",
            name="ck_workout_set_mutations_version_positive",
        ),
        sa.ForeignKeyConstraint(
            ["workout_set_id"],
            ["user_workout_sets.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "workout_set_id",
            "mutation_id",
            name="uq_workout_set_mutations_set_mutation",
        ),
    )


def downgrade() -> None:
    op.drop_table("workout_set_mutations")
    with op.batch_alter_table("user_workout_sets") as batch_op:
        batch_op.drop_constraint(
            "ck_user_workout_sets_version_positive",
            type_="check",
        )
        batch_op.drop_column("version")
