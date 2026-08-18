"""add structured split metadata for program recommendations

Revision ID: 0041_program_split
Revises: 0040_workout_set_rir
Create Date: 2026-08-18
"""

import sqlalchemy as sa

from alembic import op

revision = "0041_program_split"
down_revision = "0040_workout_set_rir"
branch_labels = None
depends_on = None

_SPLIT_BY_SLUG = {
    "strength-pplf-4d": "hybrid",
    "strength-pplf-8d": "hybrid",
    "strength-pull-legs-push-legs-4d": "hybrid",
    "strength-pull-legs-push-legs-8d": "hybrid",
    "strength-split-5d": "body_part",
    "strength-push-pull-legs-6d": "push_pull_legs",
    "strength-upper-lower-4d": "upper_lower",
    "strength-fullbody-3d": "full_body",
}


def upgrade() -> None:
    with op.batch_alter_table("program_templates") as batch_op:
        batch_op.add_column(sa.Column("split_type", sa.String(length=32), nullable=True))

    program_templates = sa.table(
        "program_templates",
        sa.column("slug", sa.String(length=64)),
        sa.column("split_type", sa.String(length=32)),
    )
    for slug, split_type in _SPLIT_BY_SLUG.items():
        op.execute(
            program_templates.update()
            .where(program_templates.c.slug == slug)
            .values(split_type=split_type)
        )

    with op.batch_alter_table("program_templates") as batch_op:
        batch_op.create_check_constraint(
            "ck_program_templates_split_type",
            "split_type IS NULL OR split_type IN "
            "('full_body', 'upper_lower', 'push_pull_legs', 'body_part', 'hybrid')",
        )


def downgrade() -> None:
    with op.batch_alter_table("program_templates") as batch_op:
        batch_op.drop_constraint("ck_program_templates_split_type", type_="check")
        batch_op.drop_column("split_type")
