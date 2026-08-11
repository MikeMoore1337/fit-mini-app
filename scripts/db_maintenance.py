"""Create and restore PostgreSQL dumps through the Compose db service.

All dump files are intentionally restricted to .artifacts/backups so operational
data cannot accidentally become a tracked repository file.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARTIFACTS = ROOT / ".artifacts"
BACKUP_DIR = ARTIFACTS / "backups"
UTC = timezone.utc  # noqa: UP017 - deployment hosts can still run Python 3.10.
BACKUP_SCRIPT = (
    "exec pg_dump --format=custom --no-owner --no-privileges "
    '--dbname="$POSTGRES_DB" --username="$POSTGRES_USER"'
)
RESTORE_SCRIPT = (
    "exec pg_restore --clean --if-exists --no-owner --no-privileges --exit-on-error "
    "--single-transaction "
    '--dbname="$POSTGRES_DB" --username="$POSTGRES_USER"'
)


def _timestamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def _artifact_path(path: Path) -> Path:
    resolved = (path if path.is_absolute() else ROOT / path).resolve()
    artifacts = ARTIFACTS.resolve()
    if not resolved.is_relative_to(artifacts):
        raise ValueError(f"backup paths must stay below {artifacts}")
    return resolved


def _compose_exec(script: str) -> list[str]:
    return ["docker", "compose", "exec", "-T", "db", "sh", "-ec", script]


def _database_name() -> str:
    result = subprocess.run(
        _compose_exec('printf "%s" "$POSTGRES_DB"'),
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    name = result.stdout.strip()
    if not name:
        raise RuntimeError("POSTGRES_DB is empty inside the db service")
    return name


def create_backup(output: Path) -> Path:
    target = _artifact_path(output)
    if target.exists():
        raise FileExistsError(f"refusing to overwrite existing backup: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_suffix(target.suffix + ".partial")

    try:
        with partial.open("xb") as stream:
            process = subprocess.run(
                _compose_exec(BACKUP_SCRIPT),
                cwd=ROOT,
                check=False,
                stdout=stream,
                stderr=subprocess.PIPE,
            )
        if process.returncode != 0:
            sys.stderr.buffer.write(process.stderr)
            raise RuntimeError(f"pg_dump failed with exit code {process.returncode}")
        partial.replace(target)
    except Exception:
        partial.unlink(missing_ok=True)
        raise
    return target


def restore_backup(source: Path, *, confirmed_database: str) -> tuple[Path, str]:
    dump = _artifact_path(source)
    if not dump.is_file():
        raise FileNotFoundError(f"backup does not exist: {dump}")

    actual_database = _database_name()
    if confirmed_database != actual_database:
        raise ValueError(
            "restore confirmation does not match POSTGRES_DB: "
            f"expected --confirm-database {actual_database!r}"
        )

    safety_backup = create_backup(BACKUP_DIR / f"pre-restore-{_timestamp()}.dump")
    with dump.open("rb") as stream:
        process = subprocess.run(
            _compose_exec(RESTORE_SCRIPT),
            cwd=ROOT,
            check=False,
            stdin=stream,
            stderr=subprocess.PIPE,
        )
    if process.returncode != 0:
        sys.stderr.buffer.write(process.stderr)
        raise RuntimeError(
            "pg_restore failed; writers must remain stopped. "
            f"The automatic safety backup is {safety_backup}"
        )
    return safety_backup, actual_database


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    backup_parser = subparsers.add_parser("backup", help="create a custom-format pg_dump")
    backup_parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="path below .artifacts/ (default: timestamped .artifacts/backups file)",
    )

    restore_parser = subparsers.add_parser(
        "restore",
        help="restore a custom-format dump after creating a safety backup",
    )
    restore_parser.add_argument("input", type=Path, help="dump file below .artifacts/")
    restore_parser.add_argument(
        "--confirm-database",
        required=True,
        help="must exactly match POSTGRES_DB inside the running db service",
    )

    args = parser.parse_args()
    try:
        if args.command == "backup":
            output = args.output or BACKUP_DIR / f"fitminiapp-{_timestamp()}.dump"
            created = create_backup(output)
            print(f"Backup created: {created}")
            return 0

        safety_backup, database = restore_backup(
            args.input,
            confirmed_database=args.confirm_database,
        )
        print(f"Database restored: {database}")
        print(f"Pre-restore safety backup: {safety_backup}")
        return 0
    except (OSError, RuntimeError, subprocess.SubprocessError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
