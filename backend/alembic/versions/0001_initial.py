"""initial schema"""

from alembic import op
import sqlalchemy as sa

revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('telegram_user_id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=64), nullable=True),
        sa.Column('first_name', sa.String(length=64), nullable=True),
        sa.Column('last_name', sa.String(length=64), nullable=True),
        sa.Column('is_coach', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('is_admin', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('ix_users_telegram_user_id', 'users', ['telegram_user_id'], unique=True)

    op.create_table('coach_clients',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('coach_user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('client_user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.UniqueConstraint('coach_user_id', 'client_user_id', name='uq_coach_client')
    )

    op.create_table('user_profiles',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('full_name', sa.String(length=128), nullable=True),
        sa.Column('goal', sa.String(length=32), nullable=True),
        sa.Column('level', sa.String(length=32), nullable=True),
        sa.Column('height_cm', sa.Integer(), nullable=True),
        sa.Column('weight_kg', sa.Integer(), nullable=True),
        sa.Column('workouts_per_week', sa.Integer(), nullable=True),
        sa.UniqueConstraint('user_id')
    )

    op.create_table('exercises',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('slug', sa.String(length=64), nullable=False),
        sa.Column('title', sa.String(length=128), nullable=False),
        sa.Column('primary_muscle', sa.String(length=64), nullable=False),
        sa.Column('equipment', sa.String(length=64), nullable=False),
    )
    op.create_index('ix_exercises_slug', 'exercises', ['slug'], unique=True)

    op.create_table('program_templates',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('slug', sa.String(length=64), nullable=False),
        sa.Column('title', sa.String(length=128), nullable=False),
        sa.Column('goal', sa.String(length=32), nullable=False),
        sa.Column('level', sa.String(length=32), nullable=False),
        sa.Column('owner_user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_by_user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('ix_program_templates_slug', 'program_templates', ['slug'], unique=True)

    op.create_table('program_template_days',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('program_id', sa.Integer(), sa.ForeignKey('program_templates.id'), nullable=False),
        sa.Column('day_number', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=128), nullable=False),
    )

    op.create_table('program_template_exercises',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('day_id', sa.Integer(), sa.ForeignKey('program_template_days.id'), nullable=False),
        sa.Column('exercise_id', sa.Integer(), sa.ForeignKey('exercises.id'), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=False),
        sa.Column('prescribed_sets', sa.Integer(), nullable=False),
        sa.Column('prescribed_reps', sa.String(length=32), nullable=False),
        sa.Column('rest_seconds', sa.Integer(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
    )

    op.create_table('user_programs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('template_id', sa.Integer(), sa.ForeignKey('program_templates.id'), nullable=False),
        sa.Column('assigned_by_user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('assigned_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
    )

    op.create_table('user_workouts',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_program_id', sa.Integer(), sa.ForeignKey('user_programs.id'), nullable=False),
        sa.Column('scheduled_date', sa.Date(), nullable=False),
        sa.Column('day_number', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=128), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='planned'),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
    )

    op.create_table('user_workout_exercises',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('workout_id', sa.Integer(), sa.ForeignKey('user_workouts.id'), nullable=False),
        sa.Column('exercise_id', sa.Integer(), sa.ForeignKey('exercises.id'), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=False),
        sa.Column('prescribed_sets', sa.Integer(), nullable=False),
        sa.Column('prescribed_reps', sa.String(length=32), nullable=False),
        sa.Column('rest_seconds', sa.Integer(), nullable=False),
    )

    op.create_table('user_workout_sets',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('workout_exercise_id', sa.Integer(), sa.ForeignKey('user_workout_exercises.id'), nullable=False),
        sa.Column('set_number', sa.Integer(), nullable=False),
        sa.Column('actual_reps', sa.Integer(), nullable=True),
        sa.Column('actual_weight', sa.Float(), nullable=True),
        sa.Column('is_completed', sa.Boolean(), nullable=False, server_default=sa.text('false')),
    )

    op.create_table('plans',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('code', sa.String(length=32), nullable=False),
        sa.Column('title', sa.String(length=128), nullable=False),
        sa.Column('price', sa.Numeric(10, 2), nullable=False),
        sa.Column('currency', sa.String(length=8), nullable=False),
        sa.Column('period_days', sa.Integer(), nullable=False),
    )
    op.create_index('ix_plans_code', 'plans', ['code'], unique=True)

    op.create_table('subscriptions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('plan_id', sa.Integer(), sa.ForeignKey('plans.id'), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('starts_at', sa.DateTime(), nullable=True),
        sa.Column('ends_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
    )

    op.create_table('payments',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('plan_id', sa.Integer(), sa.ForeignKey('plans.id'), nullable=False),
        sa.Column('provider', sa.String(length=32), nullable=False),
        sa.Column('provider_payment_id', sa.String(length=64), nullable=False),
        sa.Column('amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('currency', sa.String(length=8), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('checkout_url', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('paid_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_payments_provider_payment_id', 'payments', ['provider_payment_id'], unique=True)

    op.create_table('notification_settings',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('workout_reminders_enabled', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('reminder_hour', sa.Integer(), nullable=False, server_default='9'),
        sa.UniqueConstraint('user_id')
    )

    op.create_table('notifications',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('channel', sa.String(length=32), nullable=False),
        sa.Column('title', sa.String(length=128), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('scheduled_for', sa.DateTime(), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('last_error', sa.Text(), nullable=True),
    )


def downgrade() -> None:
    for table in ['notifications', 'notification_settings', 'payments', 'subscriptions', 'plans', 'user_workout_sets', 'user_workout_exercises', 'user_workouts', 'user_programs', 'program_template_exercises', 'program_template_days', 'program_templates', 'exercises', 'user_profiles', 'coach_clients', 'users']:
        op.drop_table(table)
