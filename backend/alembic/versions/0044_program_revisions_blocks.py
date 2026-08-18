"""add assigned program revisions and training blocks

Revision ID: 0044_program_versions
Revises: 0043_set_semantics
Create Date: 2026-08-18
"""

import sqlalchemy as sa

from alembic import op

revision = "0044_program_versions"
down_revision = "0043_set_semantics"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("user_programs") as batch_op:
        batch_op.add_column(
            sa.Column(
                "current_revision_number",
                sa.Integer(),
                server_default="0",
                nullable=False,
            )
        )
        batch_op.create_check_constraint(
            "ck_user_programs_current_revision_number",
            "current_revision_number >= 0",
        )

    op.create_table(
        "program_revisions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_program_id", sa.Integer(), nullable=False),
        sa.Column("revision_number", sa.Integer(), nullable=False),
        sa.Column("changed_by_user_id", sa.Integer(), nullable=True),
        sa.Column("actor_role", sa.String(length=16), nullable=False),
        sa.Column("change_kind", sa.String(length=32), nullable=False),
        sa.Column("reason", sa.String(length=500), nullable=True),
        sa.Column("changed_fields", sa.JSON(), nullable=False),
        sa.Column("snapshot", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "actor_role IN ('self', 'trainer', 'admin', 'system')",
            name="ck_program_revisions_actor_role",
        ),
        sa.CheckConstraint(
            "change_kind IN "
            "('assigned', 'program_archived', 'plan_updated', 'block_created', "
            "'block_updated', 'block_status_changed')",
            name="ck_program_revisions_change_kind",
        ),
        sa.CheckConstraint(
            "revision_number >= 1",
            name="ck_program_revisions_number",
        ),
        sa.ForeignKeyConstraint(["changed_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_program_id"], ["user_programs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_program_id",
            "revision_number",
            name="uq_program_revisions_program_number",
        ),
    )
    op.create_index(
        op.f("ix_program_revisions_changed_by_user_id"),
        "program_revisions",
        ["changed_by_user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_program_revisions_user_program_id"),
        "program_revisions",
        ["user_program_id"],
        unique=False,
    )

    op.create_table(
        "training_blocks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_program_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=128), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("purpose", sa.String(length=500), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_deload", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("status", sa.String(length=16), server_default="planned", nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint("end_date >= start_date", name="ck_training_blocks_dates"),
        sa.CheckConstraint("length(trim(title)) >= 1", name="ck_training_blocks_title"),
        sa.CheckConstraint("length(trim(purpose)) >= 1", name="ck_training_blocks_purpose"),
        sa.CheckConstraint(
            "status IN ('planned', 'active', 'completed', 'archived')",
            name="ck_training_blocks_status",
        ),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_program_id"], ["user_programs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_training_blocks_created_by_user_id"),
        "training_blocks",
        ["created_by_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_training_blocks_program_dates",
        "training_blocks",
        ["user_program_id", "start_date", "end_date"],
        unique=False,
    )
    op.create_index(
        "uq_training_blocks_one_active_per_program",
        "training_blocks",
        ["user_program_id"],
        unique=True,
        postgresql_where=sa.text("status = 'active'"),
        sqlite_where=sa.text("status = 'active'"),
    )

    op.create_table(
        "training_block_priority_muscles",
        sa.Column("training_block_id", sa.Integer(), nullable=False),
        sa.Column("muscle_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.CheckConstraint("position >= 0", name="ck_training_block_priority_position"),
        sa.ForeignKeyConstraint(["muscle_id"], ["muscles.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["training_block_id"], ["training_blocks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("training_block_id", "muscle_id"),
        sa.UniqueConstraint(
            "training_block_id",
            "position",
            name="uq_training_block_priority_position",
        ),
    )


def downgrade() -> None:
    op.drop_table("training_block_priority_muscles")
    op.drop_index("uq_training_blocks_one_active_per_program", table_name="training_blocks")
    op.drop_index("ix_training_blocks_program_dates", table_name="training_blocks")
    op.drop_index(op.f("ix_training_blocks_created_by_user_id"), table_name="training_blocks")
    op.drop_table("training_blocks")
    op.drop_index(op.f("ix_program_revisions_user_program_id"), table_name="program_revisions")
    op.drop_index(
        op.f("ix_program_revisions_changed_by_user_id"),
        table_name="program_revisions",
    )
    op.drop_table("program_revisions")

    with op.batch_alter_table("user_programs") as batch_op:
        batch_op.drop_constraint("ck_user_programs_current_revision_number", type_="check")
        batch_op.drop_column("current_revision_number")
