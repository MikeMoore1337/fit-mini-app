"""preserve the relocated Telegram bot support migration marker

Revision ID: 0051_bot_support_cases
Revises: 0050_comment_idempotency
Create Date: 2026-08-22
"""

revision = "0051_bot_support_cases"
down_revision = "0050_comment_idempotency"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # The original production revision already created this table at
    # 0033_bot_support_cases. Keep 0051 as a stable marker for revisions that
    # were authored after the migration was moved in the unreleased branch.
    pass


def downgrade() -> None:
    pass
