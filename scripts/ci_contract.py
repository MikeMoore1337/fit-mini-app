"""Authoritative command groups shared by GitHub CI and the local pre-push gate.

The workflow files deliberately invoke group IDs instead of carrying a second,
hand-maintained copy of the repository's quality commands.  The same registry is
also used to calculate the contract digest stored in exact-HEAD gate evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

CONTRACT_VERSION = "ci-contract-v2"
CI_SHARD_COUNT = 3
SHARDABLE_GROUPS = frozenset({"frontend-e2e", "python-tests"})
SHARD_RE = re.compile(r"(?P<number>[1-9][0-9]*)/(?P<count>[1-9][0-9]*)\Z")


class CIContractError(RuntimeError):
    """The shared CI contract cannot be executed safely."""


@dataclass(frozen=True)
class CommandSpec:
    """One reproducible command from the CI contract."""

    name: str
    argv: tuple[str, ...]
    cwd: str = "."


@dataclass(frozen=True)
class GroupSpec:
    """A named command group and its required local prerequisites."""

    name: str
    commands: tuple[CommandSpec, ...]
    prerequisites: tuple[str, ...] = ()


def _cmd(name: str, *argv: str, cwd: str = ".") -> CommandSpec:
    return CommandSpec(name=name, argv=argv, cwd=cwd)


COMMAND_GROUPS: dict[str, GroupSpec] = {
    "quality": GroupSpec(
        name="quality",
        commands=(
            _cmd(
                "pre-commit",
                "python",
                "-m",
                "pre_commit",
                "run",
                "--all-files",
                "--show-diff-on-failure",
            ),
        ),
        prerequisites=("python", "pre_commit"),
    ),
    "frontend-checks": GroupSpec(
        name="frontend-checks",
        commands=(
            _cmd("generated-api-types", "npm", "run", "api:types", cwd="frontend"),
            _cmd(
                "generated-api-types-clean",
                "git",
                "diff",
                "--exit-code",
                "--",
                "frontend/src/shared/api/schema.d.ts",
            ),
            _cmd("frontend-typecheck", "npm", "run", "typecheck", cwd="frontend"),
            _cmd("frontend-lint", "npm", "run", "lint", cwd="frontend"),
            _cmd(
                "frontend-format",
                "npx",
                "prettier",
                "--check",
                ".",
                "--end-of-line",
                "auto",
                cwd="frontend",
            ),
            _cmd("frontend-unit", "npm", "run", "test", cwd="frontend"),
            _cmd("frontend-build", "npx", "vite", "build", cwd="frontend"),
        ),
        prerequisites=("npm", "frontend/node_modules"),
    ),
    "frontend-e2e": GroupSpec(
        name="frontend-e2e",
        commands=(_cmd("frontend-e2e", "npm", "run", "e2e:ci", cwd="frontend"),),
        prerequisites=("npm", "frontend/node_modules", "frontend/playwright.config.ts"),
    ),
    "python-tests": GroupSpec(
        name="python-tests",
        commands=(
            _cmd("python-dependency-consistency", "python", "-m", "pip", "check"),
            _cmd(
                "python-suite",
                "python",
                "scripts/run_pytest.py",
                "backend/tests",
                "bot/tests",
                "-q",
                "-n",
                "4",
                "--dist=worksteal",
                "--durations=20",
            ),
        ),
        prerequisites=("python", "TEST_DATABASE_URL"),
    ),
    "migrated-stack": GroupSpec(
        name="migrated-stack",
        commands=(
            _cmd("migrations-upgrade", "python", "-m", "alembic", "upgrade", "head", cwd="backend"),
            _cmd("migrations-check", "python", "-m", "alembic", "check", cwd="backend"),
            _cmd(
                "migrated-api-smoke",
                "python",
                "scripts/run_pytest.py",
                "tests/integration/test_migrated_stack.py",
                "-q",
            ),
            _cmd("migrated-browser-smoke", "npm", "run", "e2e:migrated-stack", cwd="frontend"),
        ),
        prerequisites=("python", "alembic", "npm", "frontend/node_modules", "DATABASE_URL"),
    ),
    "dependency-audit": GroupSpec(
        name="dependency-audit",
        commands=(
            _cmd(
                "frontend-dependency-audit",
                "npm",
                "audit",
                "--omit=dev",
                "--audit-level=high",
                cwd="frontend",
            ),
            _cmd(
                "backend-dependency-audit",
                "uvx",
                "--from",
                "pip-audit==2.10.1",
                "pip-audit",
                "-r",
                "backend/requirements-runtime.txt",
            ),
            _cmd(
                "bot-dependency-audit",
                "uvx",
                "--from",
                "pip-audit==2.10.1",
                "pip-audit",
                "-r",
                "bot/requirements.txt",
            ),
        ),
        prerequisites=("npm", "uvx"),
    ),
    "policy": GroupSpec(
        name="policy",
        commands=(
            _cmd(
                "policy-tests",
                "python",
                "-m",
                "pytest",
                "tests/test_release_safeguards.py",
                "tests/test_task_session.py",
                "tests/test_pre_push_gate.py",
                "tests/test_ci_contract.py",
                "tests/test_run_task_delivery.py",
                "tests/test_deployment_contract.py",
                "tests/test_online_migrations.py",
                "tests/test_zero_downtime_deploy.py",
                "-q",
            ),
        ),
        prerequisites=("python",),
    ),
    "workflow-config": GroupSpec(
        name="workflow-config",
        commands=(_cmd("validate-contract", "python", "scripts/ci_contract.py", "validate"),),
        prerequisites=("python",),
    ),
    "image-contract": GroupSpec(
        name="image-contract",
        commands=(
            _cmd(
                "image-contract",
                "python",
                "scripts/deployment_contract.py",
                "check",
                "--ci-workflow",
                ".github/workflows/ci.yml",
                "--deploy-workflow",
                ".github/workflows/deploy.yml",
                "--compose",
                "docker-compose.yml",
            ),
        ),
        prerequisites=("python",),
    ),
    "deployment-contract": GroupSpec(
        name="deployment-contract",
        commands=(
            _cmd(
                "deployment-contract",
                "python",
                "scripts/deployment_contract.py",
                "check",
                "--ci-workflow",
                ".github/workflows/ci.yml",
                "--deploy-workflow",
                ".github/workflows/deploy.yml",
                "--compose",
                "docker-compose.yml",
                "--deploy-script",
                "scripts/deploy_production.sh",
            ),
        ),
        prerequisites=("python",),
    ),
    "container-contract": GroupSpec(
        name="container-contract",
        commands=(
            _cmd(
                "container-contract",
                "python",
                "scripts/deployment_contract.py",
                "check",
                "--ci-workflow",
                ".github/workflows/ci.yml",
                "--deploy-workflow",
                ".github/workflows/deploy.yml",
                "--compose",
                "docker-compose.yml",
            ),
        ),
        prerequisites=("python",),
    ),
}


PROFILE_GROUPS: dict[str, tuple[str, ...]] = {
    "frontend": ("quality", "frontend-checks", "frontend-e2e"),
    "backend": ("quality", "python-tests"),
    "cross-stack": (
        "quality",
        "frontend-checks",
        "frontend-e2e",
        "python-tests",
        "migrated-stack",
        "dependency-audit",
        "policy",
        "workflow-config",
        "deployment-contract",
    ),
    "workflow-platform": (
        "quality",
        "policy",
        "workflow-config",
        "image-contract",
        "deployment-contract",
    ),
    "documentation": ("quality", "workflow-config"),
}


def contract_payload() -> dict[str, object]:
    return {
        "version": CONTRACT_VERSION,
        "groups": {
            name: {
                "commands": [asdict(command) for command in spec.commands],
                "prerequisites": list(spec.prerequisites),
            }
            for name, spec in sorted(COMMAND_GROUPS.items())
        },
        "profiles": {name: list(groups) for name, groups in sorted(PROFILE_GROUPS.items())},
        "sharding": {
            "frontend-e2e": {"count": CI_SHARD_COUNT, "strategy": "playwright"},
            "python-tests": {
                "count": CI_SHARD_COUNT,
                "strategy": "pytest-node-round-robin",
            },
        },
    }


def contract_digest() -> str:
    encoded = json.dumps(
        contract_payload(), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _resolve_argv(argv: Sequence[str]) -> list[str]:
    resolved = list(argv)
    if resolved and resolved[0] == "python":
        resolved[0] = sys.executable
    elif os.name == "nt" and resolved and resolved[0] in {"npm", "npx"}:
        resolved[0] = f"{resolved[0]}.cmd"
    return resolved


def _check_prerequisite(root: Path, prerequisite: str, env: Mapping[str, str]) -> str | None:
    if prerequisite == "alembic":
        try:
            __import__("alembic")
            return None
        except ImportError:
            return "python package alembic"
    if prerequisite in {"python", "npm", "uvx", "pre_commit"}:
        executable = {
            "python": sys.executable,
            "pre_commit": "pre-commit",
        }.get(prerequisite, prerequisite)
        if prerequisite == "pre_commit":
            try:
                __import__("pre_commit")
                return None
            except ImportError:
                return "python package pre_commit"
        if shutil.which(executable) is None:
            return executable
        return None
    if prerequisite.endswith("/"):
        return None if (root / prerequisite).is_dir() else prerequisite
    if "/" in prerequisite or prerequisite.endswith((".ts", ".json", ".yml")):
        return None if (root / prerequisite).exists() else prerequisite
    return None if env.get(prerequisite) else f"environment variable {prerequisite}"


def missing_prerequisites(
    group: str, *, root: Path, env: Mapping[str, str] | None = None
) -> list[str]:
    if group not in COMMAND_GROUPS:
        raise CIContractError(f"Unknown CI command group: {group}")
    values = env or os.environ
    return [
        missing
        for prerequisite in COMMAND_GROUPS[group].prerequisites
        if (missing := _check_prerequisite(root, prerequisite, values)) is not None
    ]


def parse_shard(value: str) -> tuple[int, int]:
    """Convert a human-facing ``N/M`` shard label to a zero-based index."""

    match = SHARD_RE.fullmatch(value)
    if match is None:
        raise CIContractError(f"Invalid shard {value!r}; expected N/M with 1 <= N <= M")
    number = int(match.group("number"))
    count = int(match.group("count"))
    if number > count:
        raise CIContractError(f"Invalid shard {value!r}; shard number cannot exceed shard count")
    return number - 1, count


def select_shard(items: Sequence[str], *, shard_index: int, shard_count: int) -> tuple[str, ...]:
    """Select a deterministic round-robin subset from an ordered item list."""

    if shard_count < 1 or not 0 <= shard_index < shard_count:
        raise CIContractError(
            f"Invalid shard coordinates: index={shard_index}, count={shard_count}"
        )
    return tuple(
        item for position, item in enumerate(items) if position % shard_count == shard_index
    )


def _normalize_python_test_node(line: str) -> str | None:
    candidate = line.strip()
    path, separator, test_id = candidate.partition("::")
    if not separator:
        return None
    normalized_path = path.replace("\\", "/")
    if not normalized_path.startswith(("backend/tests/", "bot/tests/")):
        return None
    return f"{normalized_path}::{test_id}"


def _collect_python_test_nodes(root: Path, env: Mapping[str, str]) -> tuple[str, ...]:
    argv = _resolve_argv(
        (
            "python",
            "scripts/run_pytest.py",
            "backend/tests",
            "bot/tests",
            "--collect-only",
            "-q",
        )
    )
    print(f"$ (cd . && {' '.join(argv)})", flush=True)
    completed = subprocess.run(
        argv,
        cwd=root,
        env=dict(env),
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        details = "\n".join(
            part.strip() for part in (completed.stdout, completed.stderr) if part.strip()
        )
        if len(details) > 4000:
            details = details[-4000:]
        suffix = f"\n{details}" if details else ""
        raise CIContractError(
            f"Python test collection failed with exit code {completed.returncode}{suffix}"
        )

    nodes = tuple(
        normalized
        for line in completed.stdout.splitlines()
        if (normalized := _normalize_python_test_node(line)) is not None
    )
    if not nodes:
        raise CIContractError("Python test collection returned no test node IDs")
    return nodes


def _sharded_python_command(
    command: CommandSpec,
    *,
    root: Path,
    env: Mapping[str, str],
    shard_index: int,
    shard_count: int,
) -> CommandSpec:
    all_nodes = _collect_python_test_nodes(root, env)
    selected_nodes = select_shard(all_nodes, shard_index=shard_index, shard_count=shard_count)
    if not selected_nodes:
        raise CIContractError(f"No Python tests selected for shard {shard_index + 1}/{shard_count}")

    target_paths = {"backend/tests", "bot/tests"}
    target_positions = [
        position for position, argument in enumerate(command.argv) if argument in target_paths
    ]
    if not target_positions:
        raise CIContractError("Python test command has no test target paths to shard")
    first_target = min(target_positions)
    last_target = max(target_positions) + 1
    argv = (
        *command.argv[:first_target],
        *selected_nodes,
        *command.argv[last_target:],
    )
    print(
        f"Selected {len(selected_nodes)} of {len(all_nodes)} Python tests "
        f"for shard {shard_index + 1}/{shard_count}",
        flush=True,
    )
    return CommandSpec(name=f"{command.name}-shard", argv=argv, cwd=command.cwd)


def _sharded_frontend_command(
    command: CommandSpec, *, shard_index: int, shard_count: int
) -> CommandSpec:
    shard_label = f"{shard_index + 1}/{shard_count}"
    return CommandSpec(
        name=f"{command.name}-shard",
        argv=(*command.argv, "--", f"--shard={shard_label}"),
        cwd=command.cwd,
    )


def run_group(
    group: str,
    *,
    root: Path | None = None,
    env: Mapping[str, str] | None = None,
    shard: str | None = None,
) -> None:
    if group not in COMMAND_GROUPS:
        raise CIContractError(f"Unknown CI command group: {group}")
    project_root = (root or Path.cwd()).resolve()
    effective_env = dict(os.environ) | dict(env or {})
    shard_index: int | None = None
    shard_count: int | None = None
    if shard is not None:
        if group not in SHARDABLE_GROUPS:
            raise CIContractError(f"CI group {group} does not support sharding")
        shard_index, shard_count = parse_shard(shard)
    missing = missing_prerequisites(group, root=project_root, env=effective_env)
    if missing:
        raise CIContractError(f"Required prerequisite missing for {group}: {', '.join(missing)}")
    spec = COMMAND_GROUPS[group]
    for command in spec.commands:
        effective_command = command
        if shard_index is not None and shard_count is not None:
            if group == "python-tests" and command.name == "python-suite":
                effective_command = _sharded_python_command(
                    command,
                    root=project_root,
                    env=effective_env,
                    shard_index=shard_index,
                    shard_count=shard_count,
                )
            elif group == "frontend-e2e":
                effective_command = _sharded_frontend_command(
                    command, shard_index=shard_index, shard_count=shard_count
                )
        argv = _resolve_argv(effective_command.argv)
        if argv[0] == "git":
            argv = ["git", "-c", f"safe.directory={project_root.as_posix()}", *argv[1:]]
        cwd = (project_root / effective_command.cwd).resolve()
        print(f"$ (cd {effective_command.cwd} && {' '.join(argv)})", flush=True)
        completed = subprocess.run(argv, cwd=cwd, env=effective_env, check=False)
        if completed.returncode != 0:
            raise CIContractError(
                f"CI command group {group} failed at {effective_command.name} "
                f"with exit code {completed.returncode}"
            )


def validate_contract() -> None:
    if not COMMAND_GROUPS:
        raise CIContractError("CI contract has no command groups")
    for profile, groups in PROFILE_GROUPS.items():
        if not groups:
            raise CIContractError(f"CI profile {profile} is empty")
        unknown = sorted(set(groups) - set(COMMAND_GROUPS))
        if unknown:
            raise CIContractError(f"CI profile {profile} references unknown groups: {unknown}")
    for name, spec in COMMAND_GROUPS.items():
        if name != spec.name or not spec.commands:
            raise CIContractError(f"Invalid command group definition: {name}")
        command_names = [item.name for item in spec.commands]
        if len(command_names) != len(set(command_names)):
            raise CIContractError(f"Duplicate command in group {name}")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("validate")
    digest = subparsers.add_parser("digest")
    digest.add_argument("--json", action="store_true")
    groups = subparsers.add_parser("list-groups")
    groups.add_argument("--profile")
    run = subparsers.add_parser("run-group")
    run.add_argument("group", choices=sorted(COMMAND_GROUPS))
    run.add_argument("--root", type=Path, default=Path.cwd())
    run.add_argument("--shard")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        validate_contract()
        if args.command == "validate":
            print(f"CI contract valid: {CONTRACT_VERSION} {contract_digest()}")
            return 0
        if args.command == "digest":
            payload = {"version": CONTRACT_VERSION, "digest": contract_digest()}
            print(json.dumps(payload) if args.json else payload["digest"])
            return 0
        if args.command == "list-groups":
            groups = PROFILE_GROUPS.get(args.profile, tuple(COMMAND_GROUPS))
            if args.profile is not None and args.profile not in PROFILE_GROUPS:
                raise CIContractError(f"Unknown CI profile: {args.profile}")
            print(json.dumps(list(groups), ensure_ascii=False))
            return 0
        if args.command == "run-group":
            run_group(args.group, root=args.root, shard=args.shard)
            return 0
        raise AssertionError(f"Unhandled command: {args.command}")
    except (CIContractError, OSError) as error:
        print(f"ci contract error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
