"""Run the fail-closed, scope-aware local gate before the first task push."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

try:
    from scripts.ci_contract import (
        COMMAND_GROUPS,
        CONTRACT_VERSION,
        PROFILE_GROUPS,
        CIContractError,
        contract_digest,
        missing_prerequisites,
        run_group,
    )
except ModuleNotFoundError:
    from ci_contract import (  # type: ignore[no-redef]
        COMMAND_GROUPS,
        CONTRACT_VERSION,
        PROFILE_GROUPS,
        CIContractError,
        contract_digest,
        missing_prerequisites,
        run_group,
    )

TASK_BRANCH_RE = re.compile(r"^task/(?P<task_id>[0-9]+[A-Z]?)-[a-z0-9]+(?:-[a-z0-9]+)*$", re.I)
TASK_FILE_RE = re.compile(r"^(?P<task_id>[0-9]+[A-Z]?)-.+\.md$", re.I)
STATE_DIRECTORY_NAME = "codex-task-sessions-v1"


class GateError(RuntimeError):
    """The exact-HEAD local gate cannot grant a PASS."""


@dataclass(frozen=True)
class RepositoryContext:
    root: Path
    common_dir: Path
    branch: str
    head_sha: str
    task_id: str
    base_sha: str
    lease: dict[str, Any]


def _run(args: Sequence[str], *, cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    command = list(args)
    if command and command[0] == "git":
        command = ["git", "-c", f"safe.directory={cwd.resolve().as_posix()}", *command[1:]]
    completed = subprocess.run(
        command,
        cwd=cwd,
        check=False,
        text=True,
        encoding="utf-8",
        capture_output=True,
    )
    if check and completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "unknown Git error"
        raise GateError(f"Command failed ({' '.join(args)}): {detail}")
    return completed


def _git_root(start: Path) -> tuple[Path, Path]:
    root = Path(_run(["git", "rev-parse", "--show-toplevel"], cwd=start).stdout.strip()).resolve()
    common = Path(
        _run(
            ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"], cwd=root
        ).stdout.strip()
    ).resolve()
    return root, common


def _head(root: Path) -> str:
    return _run(["git", "rev-parse", "HEAD"], cwd=root).stdout.strip()


def _branch(root: Path) -> str:
    branch = _run(["git", "branch", "--show-current"], cwd=root).stdout.strip()
    if not branch:
        raise GateError("Pre-push gate requires an attached task branch")
    return branch


def _load_lease(common_dir: Path, task_id: str) -> dict[str, Any]:
    path = common_dir / STATE_DIRECTORY_NAME / "leases" / f"task-{task_id.upper()}.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise GateError(
            f"No active lease for Task {task_id}; start the task through the controller"
        ) from error
    except (OSError, json.JSONDecodeError, TypeError) as error:
        raise GateError(f"Cannot read task lease {path}: {error}") from error
    if not isinstance(payload, dict):
        raise GateError(f"Invalid task lease payload: {path}")
    return payload


def _task_document(lease: Mapping[str, Any], task_id: str) -> tuple[Path, str]:
    raw_path = str(lease.get("canonical_task_path", ""))
    path = Path(raw_path).resolve()
    if not path.is_file():
        raise GateError(f"Canonical task document is missing: {path}")
    match = TASK_FILE_RE.fullmatch(path.name)
    if match is None or match.group("task_id").upper() != task_id.upper():
        raise GateError(f"Canonical task document does not match Task {task_id}: {path}")
    return path, path.read_text(encoding="utf-8")


def _status(root: Path) -> list[str]:
    output = _run(["git", "status", "--porcelain=v1", "--untracked-files=all"], cwd=root).stdout
    return output.splitlines() if output else []


def _changed_paths(root: Path, base_sha: str, head_sha: str) -> list[str]:
    output = _run(
        ["git", "diff", "--name-status", "--find-renames", base_sha, head_sha], cwd=root
    ).stdout
    paths: list[str] = []
    for line in output.splitlines():
        fields = line.split("\t")
        if len(fields) >= 2:
            paths.extend(item.replace("\\", "/") for item in fields[1:])
    return sorted(set(paths))


def classify_scope(paths: Sequence[str]) -> dict[str, Any]:
    normalized = sorted({path.replace("\\", "/") for path in paths})
    frontend = any(path == "frontend" or path.startswith("frontend/") for path in normalized)
    backend = any(
        path == "backend" or path.startswith(("backend/", "bot/", "tests/integration/"))
        for path in normalized
    )
    workflow = any(
        path.startswith((".github/", "scripts/", "deploy/"))
        or path in {".pre-commit-config.yaml", "docker-compose.yml", "pyproject.toml"}
        for path in normalized
    )
    documentation = bool(normalized) and all(
        path.startswith(("docs/", "codex-backlog/", ".agents/"))
        or path in {"README.md", "AGENTS.md"}
        for path in normalized
    )
    if frontend and backend:
        profile = "cross-stack"
    elif workflow:
        profile = "workflow-platform"
    elif frontend:
        profile = "frontend"
    elif backend:
        profile = "backend"
    elif documentation:
        profile = "documentation"
    else:
        profile = "cross-stack"
    return {
        "profile": profile,
        "paths": normalized,
        "signals": {
            "frontend": frontend,
            "backend": backend,
            "workflow_platform": workflow,
            "documentation": documentation,
        },
        "groups": list(PROFILE_GROUPS[profile]),
    }


def _validate_base(root: Path, base_sha: str, head_sha: str) -> None:
    result = _run(["git", "merge-base", "--is-ancestor", base_sha, head_sha], cwd=root, check=False)
    if result.returncode != 0:
        raise GateError(f"HEAD {head_sha} does not descend from lease-bound master base {base_sha}")


def load_context(root: Path | None = None, *, base_sha: str | None = None) -> RepositoryContext:
    worktree_root, common_dir = _git_root((root or Path.cwd()).resolve())
    branch = _branch(worktree_root)
    match = TASK_BRANCH_RE.fullmatch(branch)
    if match is None:
        raise GateError(f"Pre-push gate requires task/<ID>-<slug>; received {branch!r}")
    if branch.split("-", maxsplit=1)[1] != branch.split("-", maxsplit=1)[1].lower():
        raise GateError(f"Pre-push gate requires task/<ID>-<slug>; received {branch!r}")
    task_id = match.group("task_id").upper()
    lease = _load_lease(common_dir, task_id)
    if lease.get("task_id") != task_id or lease.get("branch") != branch:
        raise GateError("Task branch and active lease do not match")
    leased_worktree = Path(str(lease.get("worktree", ""))).resolve()
    if leased_worktree != worktree_root:
        raise GateError(
            f"Gate is running from {worktree_root}, lease worktree is {leased_worktree}"
        )
    declared_base = str(lease.get("base_origin_master_sha", ""))
    if not declared_base:
        raise GateError("Task lease has no lease-bound master base SHA")
    if base_sha is not None and base_sha != declared_base:
        raise GateError(
            f"Requested base {base_sha} differs from lease-bound master base {declared_base}"
        )
    current_origin_master = _run(
        ["git", "rev-parse", "origin/master"], cwd=worktree_root
    ).stdout.strip()
    if current_origin_master != declared_base:
        raise GateError(
            "origin/master changed since the task lease was created; refresh the task base "
            "before pushing"
        )
    _task_document(lease, task_id)
    head_sha = _head(worktree_root)
    _validate_base(worktree_root, declared_base, head_sha)
    return RepositoryContext(
        root=worktree_root,
        common_dir=common_dir,
        branch=branch,
        head_sha=head_sha,
        task_id=task_id,
        base_sha=declared_base,
        lease=lease,
    )


def evidence_path(context: RepositoryContext) -> Path:
    repository_root = context.common_dir.parent
    return (
        repository_root
        / ".artifacts"
        / "tasks"
        / context.task_id
        / "evidence"
        / "pre-push"
        / "gate.json"
    )


def _evidence_digest(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def current_pass(context: RepositoryContext) -> dict[str, Any] | None:
    path = evidence_path(context)
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError, json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    if payload.get("evidence_version") != 1 or payload.get("contract_version") != CONTRACT_VERSION:
        return None
    if payload.get("terminal_result") != "PRE_PUSH_CI_PASS":
        return None
    if payload.get("head_sha") != context.head_sha or payload.get("base_sha") != context.base_sha:
        return None
    if payload.get("branch") != context.branch or payload.get("task_id") != context.task_id:
        return None
    if payload.get("target_base_branch") != "master":
        return None
    if (
        payload.get("contract_digest") != contract_digest()
        or payload.get("clean_worktree") is not True
    ):
        return None
    if not payload.get("started_at") or not payload.get("finished_at"):
        return None
    gates = payload.get("gates")
    if (
        not isinstance(gates, list)
        or not gates
        or any(
            not isinstance(gate, dict)
            or gate.get("applicable") is not True
            or gate.get("status") != "SUCCESS"
            for gate in gates
        )
    ):
        return None
    evidence_digest = payload.get("evidence_digest")
    unsigned_payload = dict(payload)
    unsigned_payload.pop("evidence_digest", None)
    if not isinstance(evidence_digest, str) or evidence_digest != _evidence_digest(
        unsigned_payload
    ):
        return None
    if _status(context.root):
        return None
    return payload


def run_gate(context: RepositoryContext, *, execute: bool = True) -> dict[str, Any]:
    dirty = _status(context.root)
    if dirty:
        raise GateError("Exact-HEAD pre-push gate requires a clean worktree: " + "; ".join(dirty))
    paths = _changed_paths(context.root, context.base_sha, context.head_sha)
    scope = classify_scope(paths)
    now = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
    payload: dict[str, Any] = {
        "evidence_version": 1,
        "contract_version": CONTRACT_VERSION,
        "contract_digest": contract_digest(),
        "task_id": context.task_id,
        "branch": context.branch,
        "head_sha": context.head_sha,
        "base_sha": context.base_sha,
        "target_base_branch": "master",
        "scope": scope,
        "clean_worktree": True,
        "started_at": now,
        "finished_at": None,
        "gates": [],
        "terminal_result": "PLAN_ONLY" if not execute else "PRE_PUSH_CI_FAILED",
        "task_evidence_reference": str(evidence_path(context)),
    }
    for group in scope["groups"]:
        missing = missing_prerequisites(group, root=context.root, env=os.environ)
        gate_record: dict[str, Any] = {
            "group": group,
            "applicable": True,
            "commands": [item.name for item in COMMAND_GROUPS[group].commands],
            "status": "BLOCKED" if missing else "PENDING",
            "missing_prerequisites": missing,
        }
        payload["gates"].append(gate_record)
        if not execute:
            continue
        if missing:
            payload["terminal_result"] = "PRE_PUSH_CI_BLOCKED"
            break
        try:
            run_group(group, root=context.root)
        except (CIContractError, OSError) as error:
            gate_record["status"] = "FAILED"
            gate_record["error"] = str(error)
            payload["terminal_result"] = "PRE_PUSH_CI_FAILED"
            break
        gate_record["status"] = "SUCCESS"
    if execute and payload["terminal_result"] not in {"PRE_PUSH_CI_BLOCKED", "PRE_PUSH_CI_FAILED"}:
        if _status(context.root):
            payload["terminal_result"] = "PRE_PUSH_CI_FAILED"
            payload["clean_worktree"] = False
        else:
            payload["terminal_result"] = "PRE_PUSH_CI_PASS"
    payload["finished_at"] = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
    payload["evidence_digest"] = _evidence_digest(payload)
    destination = evidence_path(context)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return payload


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-sha")
    parser.add_argument("--plan", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        context = load_context(base_sha=args.base_sha)
        payload = run_gate(context, execute=not args.plan)
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(f"{payload['terminal_result']}: {context.task_id} {context.head_sha}")
        return 0 if payload["terminal_result"] in {"PRE_PUSH_CI_PASS", "PLAN_ONLY"} else 1
    except (GateError, OSError, json.JSONDecodeError) as error:
        print(f"pre-push gate error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
