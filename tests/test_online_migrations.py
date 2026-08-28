from pathlib import Path

import pytest
from scripts.check_online_migrations import OnlineMigrationError, validate_added_migration


def _migration(path: Path, body: str) -> Path:
    path.write_text(body, encoding="utf-8")
    return path


def test_online_migration_accepts_declared_additive_expand(tmp_path: Path) -> None:
    path = _migration(
        tmp_path / "0064_expand.py",
        'online_rollout_phase = "expand"\n'
        'online_rollout_notes = "Nullable additive column; metadata-only lock."\n\n'
        "def upgrade():\n"
        '    op.add_column("users", sa.Column("nickname", sa.String(), nullable=True))\n'
        '\ndef downgrade():\n    op.drop_column("users", "nickname")\n',
    )

    validate_added_migration(path)


@pytest.mark.parametrize("operation", ["drop_table", "drop_column", "alter_column"])
def test_online_migration_rejects_destructive_contract_operation(
    tmp_path: Path, operation: str
) -> None:
    path = _migration(
        tmp_path / "0064_contract.py",
        f'online_rollout_phase = "expand"\n'
        f'online_rollout_notes = "reviewed"\n\ndef upgrade():\n    op.{operation}("users")\n',
    )

    with pytest.raises(OnlineMigrationError, match="destructive operations"):
        validate_added_migration(path)


def test_online_backfill_requires_bounded_idempotency_notes(tmp_path: Path) -> None:
    path = _migration(
        tmp_path / "0064_backfill.py",
        'online_rollout_phase = "backfill"\n\ndef upgrade():\n    op.execute("UPDATE users")\n',
    )

    with pytest.raises(OnlineMigrationError, match="online_rollout_notes"):
        validate_added_migration(path)


def test_online_backfill_rejects_destructive_sql(tmp_path: Path) -> None:
    path = _migration(
        tmp_path / "0064_backfill.py",
        'online_rollout_phase = "backfill"\n'
        'online_rollout_notes = "bounded by primary key batches"\n\n'
        "online_rollout_batch_size = 1000\n"
        "online_rollout_idempotent = True\n\n"
        'def upgrade():\n    op.execute("DELETE FROM users")\n',
    )

    with pytest.raises(OnlineMigrationError, match="destructive SQL"):
        validate_added_migration(path)


def test_online_backfill_accepts_explicit_bounded_idempotent_update(tmp_path: Path) -> None:
    path = _migration(
        tmp_path / "0064_backfill.py",
        'online_rollout_phase = "backfill"\n'
        'online_rollout_notes = "bounded deterministic update by primary key window"\n'
        "online_rollout_batch_size = 1000\n"
        "online_rollout_idempotent = True\n\n"
        "def upgrade():\n"
        '    op.execute("UPDATE users SET normalized = TRUE WHERE id >= 1 AND id < 1001")\n',
    )

    validate_added_migration(path)


def test_online_backfill_rejects_unbounded_update(tmp_path: Path) -> None:
    path = _migration(
        tmp_path / "0064_backfill.py",
        'online_rollout_phase = "backfill"\n'
        'online_rollout_notes = "claimed bounded update"\n'
        "online_rollout_batch_size = 1000\n"
        "online_rollout_idempotent = True\n\n"
        'def upgrade():\n    op.execute("UPDATE users SET normalized = TRUE")\n',
    )

    with pytest.raises(OnlineMigrationError, match="bounded UPDATE"):
        validate_added_migration(path)


@pytest.mark.parametrize("method", ["execute", "exec_driver_sql"])
def test_online_migration_rejects_sql_execution_outside_op_contract(
    tmp_path: Path, method: str
) -> None:
    path = _migration(
        tmp_path / "0064_raw_connection.py",
        'online_rollout_phase = "expand"\n'
        'online_rollout_notes = "reviewed"\n\n'
        "def upgrade():\n"
        "    connection = context.get_bind()\n"
        f'    connection.{method}(sa.text("DROP TABLE users"))\n',
    )

    with pytest.raises(OnlineMigrationError, match=r"outside the verified op\.execute"):
        validate_added_migration(path)


def test_online_migration_rejects_destructive_top_level_helper(tmp_path: Path) -> None:
    path = _migration(
        tmp_path / "0064_helper.py",
        'online_rollout_phase = "expand"\n'
        'online_rollout_notes = "reviewed"\n\n'
        'def destroy():\n    op.drop_table("users")\n\n'
        "def upgrade():\n    destroy()\n",
    )

    with pytest.raises(OnlineMigrationError, match="outside the 'expand' online allowlist"):
        validate_added_migration(path)


@pytest.mark.parametrize(
    "operation",
    [
        'op.create_index("ix_users_email", "users", ["email"])',
        'op.create_unique_constraint("uq_users_email", "users", ["email"])',
        'op.create_foreign_key("fk_users_team", "users", "teams", ["team_id"], ["id"])',
    ],
)
def test_online_expand_rejects_lock_prone_operations(tmp_path: Path, operation: str) -> None:
    path = _migration(
        tmp_path / "0064_locking.py",
        'online_rollout_phase = "expand"\n'
        'online_rollout_notes = "reviewed"\n\n'
        f"def upgrade():\n    {operation}\n",
    )

    with pytest.raises(OnlineMigrationError, match="lock-prone operations"):
        validate_added_migration(path)


@pytest.mark.parametrize(
    "column",
    [
        'sa.Column("nickname", sa.String(), nullable=False)',
        'sa.Column("nickname", sa.String(), nullable=True, server_default="")',
        'sa.Column("nickname", sa.String(), nullable=True, unique=True)',
        'sa.Column("nickname", sa.String(), nullable=True, index=True)',
    ],
)
def test_online_expand_rejects_rewrite_or_constraint_add_column(
    tmp_path: Path, column: str
) -> None:
    path = _migration(
        tmp_path / "0064_unsafe_column.py",
        'online_rollout_phase = "expand"\n'
        'online_rollout_notes = "reviewed"\n\n'
        f'def upgrade():\n    op.add_column("users", {column})\n',
    )

    with pytest.raises(OnlineMigrationError, match="add_column"):
        validate_added_migration(path)


def test_online_expand_rejects_positional_foreign_key_in_add_column(tmp_path: Path) -> None:
    path = _migration(
        tmp_path / "0064_foreign_key.py",
        'online_rollout_phase = "expand"\n'
        'online_rollout_notes = "reviewed"\n\n'
        "def upgrade():\n"
        '    op.add_column("users", sa.Column("team_id", sa.Integer(), '
        'sa.ForeignKey("teams.id"), nullable=True))\n',
    )

    with pytest.raises(OnlineMigrationError, match="positional constraints"):
        validate_added_migration(path)


def test_online_expand_rejects_two_argument_foreign_key_column(tmp_path: Path) -> None:
    path = _migration(
        tmp_path / "0064_foreign_key_only.py",
        'online_rollout_phase = "expand"\n'
        'online_rollout_notes = "reviewed"\n\n'
        "def upgrade():\n"
        '    op.add_column("users", sa.Column("team_id", '
        'sa.ForeignKey("teams.id"), nullable=True))\n',
    )

    with pytest.raises(OnlineMigrationError, match="allowlisted static SQLAlchemy scalar type"):
        validate_added_migration(path)
