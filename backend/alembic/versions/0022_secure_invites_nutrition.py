"""secure coach invites and nutrition ownership

Revision ID: 0022_secure_invites_nutrition
Revises: 0021_coach_client_private_name
Create Date: 2026-08-02
"""

import sqlalchemy as sa

from alembic import op

revision = "0022_secure_invites_nutrition"
down_revision = "0021_coach_client_private_name"
branch_labels = None
depends_on = None

FK_NAMING_CONVENTION = {"fk": "%(table_name)s_%(column_0_name)s_fkey"}


def upgrade() -> None:
    connection = op.get_bind()

    connection.execute(
        sa.text(
            """
            INSERT INTO notification_settings (
                user_id,
                workout_reminders_enabled,
                reminder_hour
            )
            SELECT users.id, true, 9
            FROM users
            WHERE NOT EXISTS (
                SELECT 1
                FROM notification_settings
                WHERE notification_settings.user_id = users.id
            )
            """
        )
    )

    # Legacy identifier-based invitations have no secret that the recipient can
    # prove possession of. Revoke them before making the invariant enforceable.
    connection.execute(
        sa.text(
            """
            UPDATE notifications
            SET status = 'cancelled'
            WHERE status = 'queued'
              AND dedupe_key IN (
                  SELECT 'trainer_request:' || id
                  FROM coach_client_invites
                  WHERE status = 'pending' AND token_hash IS NULL
              )
            """
        )
    )
    connection.execute(
        sa.text(
            """
            UPDATE coach_client_invites
            SET status = 'revoked'
            WHERE status = 'pending' AND token_hash IS NULL
            """
        )
    )
    with op.batch_alter_table("coach_client_invites") as batch_op:
        batch_op.create_check_constraint(
            "ck_coach_client_invites_pending_token",
            "status <> 'pending' OR token_hash IS NOT NULL",
        )

    # Stable client codes linked accounts without explicit confirmation of a
    # specific trainer. One-time invitation tokens replace that legacy flow.
    op.drop_index("ix_users_client_code", table_name="users")
    op.drop_column("users", "client_code")

    with op.batch_alter_table(
        "nutrition_targets", naming_convention=FK_NAMING_CONVENTION
    ) as batch_op:
        batch_op.drop_constraint("nutrition_targets_user_id_fkey", type_="foreignkey")
        batch_op.drop_constraint("nutrition_targets_assigned_by_user_id_fkey", type_="foreignkey")
        batch_op.create_foreign_key(
            "nutrition_targets_user_id_fkey",
            "users",
            ["user_id"],
            ["id"],
            ondelete="CASCADE",
        )
        batch_op.create_foreign_key(
            "nutrition_targets_assigned_by_user_id_fkey",
            "users",
            ["assigned_by_user_id"],
            ["id"],
            ondelete="SET NULL",
        )
    with op.batch_alter_table("user_profiles") as batch_op:
        batch_op.alter_column(
            "weight_kg",
            existing_type=sa.Integer(),
            type_=sa.Float(),
            existing_nullable=True,
            postgresql_using="weight_kg::double precision",
        )


def downgrade() -> None:
    op.add_column("users", sa.Column("client_code", sa.String(length=8), nullable=True))
    op.create_index("ix_users_client_code", "users", ["client_code"], unique=True)
    with op.batch_alter_table("user_profiles") as batch_op:
        batch_op.alter_column(
            "weight_kg",
            existing_type=sa.Float(),
            type_=sa.Integer(),
            existing_nullable=True,
            postgresql_using="weight_kg::integer",
        )
    with op.batch_alter_table(
        "nutrition_targets", naming_convention=FK_NAMING_CONVENTION
    ) as batch_op:
        batch_op.drop_constraint("nutrition_targets_assigned_by_user_id_fkey", type_="foreignkey")
        batch_op.drop_constraint("nutrition_targets_user_id_fkey", type_="foreignkey")
        batch_op.create_foreign_key(
            "nutrition_targets_assigned_by_user_id_fkey",
            "users",
            ["assigned_by_user_id"],
            ["id"],
        )
        batch_op.create_foreign_key(
            "nutrition_targets_user_id_fkey",
            "users",
            ["user_id"],
            ["id"],
        )
    with op.batch_alter_table("coach_client_invites") as batch_op:
        batch_op.drop_constraint("ck_coach_client_invites_pending_token", type_="check")
