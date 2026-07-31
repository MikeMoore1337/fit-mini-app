"""add per-user hidden program examples

Revision ID: 0017_hidden_templates
Revises: 0016_nutrition_activity
Create Date: 2026-07-31
"""

import sqlalchemy as sa

from alembic import op

revision = "0017_hidden_templates"
down_revision = "0016_nutrition_activity"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "hidden_program_templates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "template_id",
            sa.Integer(),
            sa.ForeignKey("program_templates.id"),
            nullable=False,
        ),
        sa.Column("hidden_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "template_id", name="uq_hidden_program_template"),
    )
    op.create_index(
        "ix_hidden_program_templates_user_id",
        "hidden_program_templates",
        ["user_id"],
    )
    op.create_index(
        "ix_hidden_program_templates_template_id",
        "hidden_program_templates",
        ["template_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_hidden_program_templates_template_id",
        table_name="hidden_program_templates",
    )
    op.drop_index(
        "ix_hidden_program_templates_user_id",
        table_name="hidden_program_templates",
    )
    op.drop_table("hidden_program_templates")
