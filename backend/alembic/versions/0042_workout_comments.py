"""add contextual trainer workout comments

Revision ID: 0042_workout_comments
Revises: 0041_program_split
Create Date: 2026-08-18
"""

import sqlalchemy as sa

from alembic import op

revision = "0042_workout_comments"
down_revision = "0041_program_split"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("notifications") as batch_op:
        batch_op.add_column(sa.Column("action_url", sa.String(length=512), nullable=True))
        batch_op.create_check_constraint(
            "ck_notifications_internal_action_url",
            "action_url IS NULL OR action_url = '/app' OR action_url LIKE '/app?%'",
        )

    op.create_table(
        "workout_comments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("coach_client_id", sa.Integer(), nullable=False),
        sa.Column("trainer_author_id", sa.Integer(), nullable=False),
        sa.Column("client_user_id", sa.Integer(), nullable=False),
        sa.Column("workout_id", sa.Integer(), nullable=False),
        sa.Column("workout_exercise_id", sa.Integer(), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint(
            "length(body) BETWEEN 1 AND 2000",
            name="ck_workout_comments_body_length",
        ),
        sa.ForeignKeyConstraint(
            ["coach_client_id"], ["coach_clients.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["trainer_author_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["client_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workout_id"], ["user_workouts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["workout_exercise_id"],
            ["user_workout_exercises.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_workout_comments_client_workout_created",
        "workout_comments",
        ["client_user_id", "workout_id", "created_at", "id"],
        unique=False,
    )
    op.create_index(
        "ix_workout_comments_relation_workout_created",
        "workout_comments",
        ["coach_client_id", "workout_id", "created_at", "id"],
        unique=False,
    )

    op.create_table(
        "workout_comment_revisions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("comment_id", sa.Integer(), nullable=False),
        sa.Column("revision_number", sa.Integer(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("edited_by_user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "length(body) BETWEEN 1 AND 2000",
            name="ck_workout_comment_revisions_body_length",
        ),
        sa.ForeignKeyConstraint(
            ["comment_id"], ["workout_comments.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["edited_by_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "comment_id",
            "revision_number",
            name="uq_workout_comment_revisions_comment_number",
        ),
    )
    op.create_index(
        op.f("ix_workout_comment_revisions_comment_id"),
        "workout_comment_revisions",
        ["comment_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_workout_comment_revisions_comment_id"),
        table_name="workout_comment_revisions",
    )
    op.drop_table("workout_comment_revisions")
    op.drop_index(
        "ix_workout_comments_relation_workout_created", table_name="workout_comments"
    )
    op.drop_index(
        "ix_workout_comments_client_workout_created", table_name="workout_comments"
    )
    op.drop_table("workout_comments")

    with op.batch_alter_table("notifications") as batch_op:
        batch_op.drop_constraint("ck_notifications_internal_action_url", type_="check")
        batch_op.drop_column("action_url")
