"""Fail-closed task worktree, lease, integration and provenance controller.

Runtime coordination state lives in the shared Git common directory.  The state is
therefore visible from every worktree but is never part of a commit.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

TASK_ID_PATTERN = r"[0-9]+[A-Z]?"
TASK_ID_RE = re.compile(rf"^{TASK_ID_PATTERN}$")
TASK_BRANCH_RE = re.compile(
    rf"^task/(?P<task_id>{TASK_ID_PATTERN})-(?P<slug>[a-z0-9]+(?:-[a-z0-9]+)*)$"
)
TASK_COMMIT_RE = re.compile(rf"\[Task (?P<task_id>{TASK_ID_PATTERN})\]")
TASK_FILE_RE = re.compile(rf"^(?P<task_id>{TASK_ID_PATTERN})-(?P<slug>.+)\.md$")
TASK_STATE_VERSION = 1
STATE_DIRECTORY_NAME = "codex-task-sessions-v1"
SYNC_APP_CONFIG_PATH = Path(".github/deployed-sync-app.json")
VALID_CHECK_CONCLUSIONS = {"SUCCESS"}
FAILED_CHECK_CONCLUSIONS = {
    "ACTION_REQUIRED",
    "CANCELLED",
    "FAILURE",
    "SKIPPED",
    "STALE",
    "STARTUP_FAILURE",
    "TIMED_OUT",
}
UMBRELLA_TASK_IDS = {"90", "92", "93", "94", "95", "99", "100", "126"}


class TaskSessionError(RuntimeError):
    """A fail-closed controller refusal with an actionable message."""


def utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def normalize_task_id(value: str) -> str:
    task_id = value.strip().upper()
    if not TASK_ID_RE.fullmatch(task_id):
        raise TaskSessionError(f"Invalid task ID: {value!r}")
    return task_id


def task_id_from_branch(branch: str) -> str:
    match = TASK_BRANCH_RE.fullmatch(branch)
    if match is None:
        raise TaskSessionError(f"Branch {branch!r} must match task/<ID>-<lowercase-kebab-slug>")
    return match.group("task_id")


def normalize_concurrency_class(value: str) -> str:
    concurrency_class = value.strip().lower()
    if concurrency_class in {"exclusive-write", "independent-write"}:
        return concurrency_class
    raise TaskSessionError("Concurrency must be exclusive-write or independent-write")


def write_lanes_compatible(first: str, second: str) -> bool:
    left = normalize_concurrency_class(first)
    right = normalize_concurrency_class(second)
    return left == right == "independent-write"


def validate_task_commit_messages(task_id: str, messages: Sequence[str]) -> None:
    expected = normalize_task_id(task_id)
    if not messages:
        raise TaskSessionError("Task branch contains no task commits")
    for message in messages:
        ids = {match.group("task_id") for match in TASK_COMMIT_RE.finditer(message)}
        if ids != {expected}:
            headline = message.splitlines()[0] if message else "<empty>"
            raise TaskSessionError(f"Commit {headline!r} must contain exactly [Task {expected}]")


def _run(
    args: Sequence[str],
    *,
    cwd: Path,
    check: bool = True,
    env: Mapping[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        list(args),
        cwd=cwd,
        check=False,
        text=True,
        encoding="utf-8",
        capture_output=True,
        env=dict(os.environ) | dict(env or {}),
    )
    if check and completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "unknown error"
        raise TaskSessionError(f"Command failed ({' '.join(args)}): {detail}")
    return completed


@dataclass(frozen=True)
class Worktree:
    path: Path
    head: str
    branch: str | None
    detached: bool


@dataclass(frozen=True)
class TaskDocument:
    task_id: str
    path: Path
    slug: str
    status: str
    dependencies: tuple[str, ...]
    executable: bool
    concurrency_class: str
    owner_gate: str
    integration_policy: str


class GitRepository:
    def __init__(self, start: Path) -> None:
        self.start = start.resolve()
        top = _run(["git", "rev-parse", "--show-toplevel"], cwd=self.start).stdout.strip()
        self.current_worktree = Path(top).resolve()
        common = _run(
            ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
            cwd=self.start,
        ).stdout.strip()
        self.common_dir = Path(common).resolve()

    def git(self, *args: str, cwd: Path | None = None, check: bool = True) -> str:
        return _run(["git", *args], cwd=cwd or self.current_worktree, check=check).stdout.strip()

    def worktrees(self) -> list[Worktree]:
        output = self.git("worktree", "list", "--porcelain")
        records: list[Worktree] = []
        current: dict[str, str] = {}
        for line in [*output.splitlines(), ""]:
            if line:
                key, _, value = line.partition(" ")
                current[key] = value
                continue
            if not current:
                continue
            branch = current.get("branch")
            records.append(
                Worktree(
                    path=Path(current["worktree"]).resolve(),
                    head=current.get("HEAD", ""),
                    branch=branch.removeprefix("refs/heads/") if branch else None,
                    detached="detached" in current,
                )
            )
            current = {}
        return records

    def canonical_dev_worktree(self) -> Worktree:
        matches = [item for item in self.worktrees() if item.branch == "dev"]
        if len(matches) != 1:
            raise TaskSessionError(f"Expected exactly one main dev worktree, found {len(matches)}")
        return matches[0]

    def ref(self, name: str) -> str:
        return self.git("rev-parse", "--verify", name)

    def ref_exists(self, name: str) -> bool:
        return self.git("rev-parse", "--verify", "--quiet", name, check=False) != ""

    def is_ancestor(self, ancestor: str, descendant: str) -> bool:
        completed = _run(
            ["git", "merge-base", "--is-ancestor", ancestor, descendant],
            cwd=self.current_worktree,
            check=False,
        )
        return completed.returncode == 0

    def status(self, path: Path) -> list[str]:
        output = self.git("status", "--porcelain=v1", "--untracked-files=all", cwd=path)
        return output.splitlines() if output else []

    def ahead_behind(self, left: str, right: str) -> tuple[int, int]:
        output = self.git("rev-list", "--left-right", "--count", f"{left}...{right}")
        ahead, behind = output.split()
        return int(ahead), int(behind)

    def git_dir(self, path: Path) -> Path:
        output = self.git("rev-parse", "--path-format=absolute", "--git-dir", cwd=path)
        return Path(output).resolve()

    def operation_issues(self, path: Path) -> list[str]:
        git_dir = self.git_dir(path)
        markers = (
            "index.lock",
            "MERGE_HEAD",
            "CHERRY_PICK_HEAD",
            "REVERT_HEAD",
            "BISECT_START",
            "rebase-apply",
            "rebase-merge",
        )
        return [marker for marker in markers if (git_dir / marker).exists()]

    def commits(self, revision_range: str) -> list[str]:
        output = self.git("log", "--format=%B%x00", revision_range, check=False)
        return [message.strip() for message in output.split("\x00") if message.strip()]

    def unique_commits(self, branch: str, base: str = "origin/dev") -> list[str]:
        output = self.git("log", "--oneline", f"{base}..{branch}", check=False)
        return output.splitlines() if output else []

    def detached_unique_commits(self, path: Path) -> list[str]:
        output = self.git("log", "--oneline", "HEAD", "--not", "--all", cwd=path, check=False)
        return output.splitlines() if output else []

    def upstream(self, branch: str) -> str | None:
        completed = _run(
            [
                "git",
                "rev-parse",
                "--abbrev-ref",
                "--symbolic-full-name",
                f"{branch}@{{upstream}}",
            ],
            cwd=self.current_worktree,
            check=False,
        )
        return completed.stdout.strip() if completed.returncode == 0 else None

    def local_branches(self) -> list[dict[str, str | None]]:
        output = self.git(
            "for-each-ref",
            "--format=%(refname:short)%00%(objectname)%00%(upstream:short)",
            "refs/heads",
        )
        result: list[dict[str, str | None]] = []
        for line in output.splitlines():
            name, sha, upstream = line.split("\x00")
            result.append({"branch": name, "sha": sha, "upstream": upstream or None})
        return result

    def create_task_worktree(self, branch: str, path: Path, base_sha: str) -> None:
        self.git("branch", branch, base_sha)
        try:
            self.git("worktree", "add", str(path), branch)
        except Exception:
            self.git("branch", "-D", branch, check=False)
            raise


def _extract_bold_field(text: str, name: str) -> str:
    pattern = re.compile(rf"^- \*\*{re.escape(name)}:\*\*\s*(.+)$", re.MULTILINE)
    match = pattern.search(text)
    return match.group(1).strip() if match else ""


def _legacy_dependencies(text: str, current_task_id: str) -> tuple[str, ...]:
    value = _extract_bold_field(text, "Зависимости")
    if not value:
        return ()
    candidates = {
        match.group(0)
        for match in re.finditer(TASK_ID_PATTERN, value.upper())
        if match.group(0) != current_task_id
    }
    return tuple(sorted(candidates))


def _metadata_block(text: str) -> dict[str, str]:
    match = re.search(r"<!--\s*task-session\s*(.*?)-->", text, flags=re.DOTALL)
    if match is None:
        return {}
    result: dict[str, str] = {}
    for raw_line in match.group(1).splitlines():
        key, separator, value = raw_line.partition(":")
        if separator:
            result[key.strip()] = value.strip()
    return result


def find_task_document(canonical_root: Path, task_id: str) -> TaskDocument:
    expected = normalize_task_id(task_id)
    roots = (
        canonical_root / "codex-backlog" / "tasks",
        canonical_root / "codex-backlog" / "bugs" / "pending",
        canonical_root / "codex-backlog" / "telegram-core-release-backlog" / "tasks",
    )
    matches: list[Path] = []
    for root in roots:
        if root.is_dir():
            matches.extend(
                path
                for path in root.glob(f"{expected}-*.md")
                if "done" not in path.relative_to(root).parts
            )
    if len(matches) != 1:
        raise TaskSessionError(
            f"Expected one canonical pending task for {expected}, found {len(matches)}"
        )
    path = matches[0].resolve()
    filename_match = TASK_FILE_RE.fullmatch(path.name)
    if filename_match is None:
        raise TaskSessionError(f"Invalid task filename: {path.name}")
    text = path.read_text(encoding="utf-8")
    metadata = _metadata_block(text)
    status = _extract_bold_field(text, "Статус")
    task_type = _extract_bold_field(text, "Тип").lower()
    executable_default = expected not in UMBRELLA_TASK_IDS and "umbrella" not in task_type
    executable = metadata.get("executable", str(executable_default)).lower() == "true"
    dependencies_value = metadata.get("dependencies")
    dependencies = (
        tuple(normalize_task_id(item) for item in dependencies_value.split(",") if item.strip())
        if dependencies_value is not None
        else _legacy_dependencies(text, expected)
    )
    slug = re.sub(r"[^a-z0-9]+", "-", filename_match.group("slug").lower()).strip("-")
    return TaskDocument(
        task_id=expected,
        path=path,
        slug=slug,
        status=status,
        dependencies=dependencies,
        executable=executable,
        concurrency_class=normalize_concurrency_class(
            metadata.get("concurrency", "exclusive-write")
        ),
        owner_gate=metadata.get("owner_gate", "explicit-launch"),
        integration_policy=metadata.get("integration", "task-pr-to-dev"),
    )


class StateStore:
    def __init__(self, common_dir: Path) -> None:
        self.root = common_dir / STATE_DIRECTORY_NAME
        self.leases = self.root / "leases"
        self.history = self.root / "history"
        self.queue_path = self.root / "integration-queue.json"
        self.lock_path = self.root / "state.lock"

    def initialize(self) -> None:
        self.leases.mkdir(parents=True, exist_ok=True)
        self.history.mkdir(parents=True, exist_ok=True)
        contract = self.root / "contract.json"
        if not contract.exists():
            self.create_json(
                contract,
                {"version": TASK_STATE_VERSION, "created_at": utc_now()},
            )

    @contextmanager
    def lock(self) -> Iterator[None]:
        self.root.mkdir(parents=True, exist_ok=True)
        try:
            descriptor = os.open(self.lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError as error:
            raise TaskSessionError(
                f"Coordination state is locked: {self.lock_path}; run recover, do not delete it"
            ) from error
        try:
            os.write(descriptor, f"pid={os.getpid()} created_at={utc_now()}\n".encode())
            os.close(descriptor)
            yield
        finally:
            self.lock_path.unlink(missing_ok=True)

    @staticmethod
    def read_json(path: Path, default: Any = None) -> Any:
        if not path.exists():
            return default
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise TaskSessionError(f"Corrupted coordination state {path}: {error}") from error

    def create_json(self, path: Path, payload: Mapping[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError as error:
            raise TaskSessionError(f"State already exists: {path}") from error
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")

    @staticmethod
    def replace_json(path: Path, payload: Mapping[str, Any] | Sequence[Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
        )
        temporary = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=2)
                handle.write("\n")
            temporary.replace(path)
        finally:
            temporary.unlink(missing_ok=True)

    def task_lease_path(self, task_id: str) -> Path:
        return self.leases / f"task-{normalize_task_id(task_id)}.json"

    def mode_lease_path(self, mode: str) -> Path:
        return self.leases / f"{mode}.json"

    def all_leases(self) -> list[dict[str, Any]]:
        if not self.leases.exists():
            return []
        return [self.read_json(path) for path in sorted(self.leases.glob("*.json"))]


class GitHubClient:
    def __init__(self, repository: GitRepository, repo_slug: str | None = None) -> None:
        self.repository = repository
        self.repo_slug = repo_slug or self._repo_slug()

    def _repo_slug(self) -> str:
        remote = self.repository.git("remote", "get-url", "origin")
        match = re.search(r"github\.com[/:](?P<slug>[^/]+/[^/.]+)(?:\.git)?$", remote)
        if match is None:
            raise TaskSessionError(f"Cannot derive GitHub repository from origin URL: {remote}")
        return match.group("slug")

    def api(self, endpoint: str) -> Any:
        result = _run(
            ["gh", "api", f"repos/{self.repo_slug}/{endpoint}"],
            cwd=self.repository.current_worktree,
        )
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError as error:
            raise TaskSessionError(f"GitHub returned invalid JSON for {endpoint}") from error

    def open_pull_requests(self) -> list[dict[str, Any]]:
        payload = self.api("pulls?state=open&per_page=100")
        return list(payload)

    def pull_request(self, number: int) -> dict[str, Any]:
        return dict(self.api(f"pulls/{number}"))

    def pull_request_commits(self, number: int) -> list[dict[str, Any]]:
        return list(self.api(f"pulls/{number}/commits?per_page=100"))

    def pull_request_files(self, number: int) -> list[dict[str, Any]]:
        files: list[dict[str, Any]] = []
        page = 1
        while True:
            batch = list(self.api(f"pulls/{number}/files?per_page=100&page={page}"))
            files.extend(batch)
            if len(batch) < 100:
                return files
            page += 1

    def check_runs(self, sha: str) -> list[dict[str, Any]]:
        payload = self.api(f"commits/{sha}/check-runs?per_page=100")
        return list(payload.get("check_runs", []))

    def workflow_runs(self, workflow: str, sha: str) -> list[dict[str, Any]]:
        payload = self.api(f"actions/workflows/{workflow}/runs?head_sha={sha}&per_page=100")
        return list(payload.get("workflow_runs", []))

    def branch_head(self, branch: str) -> str:
        payload = self.api(f"git/ref/heads/{branch}")
        return str(payload["object"]["sha"])

    def active_workflow_runs(self) -> list[dict[str, Any]]:
        payload = self.api("actions/runs?per_page=100")
        active_statuses = {"queued", "in_progress", "pending", "requested", "waiting"}
        return [
            item
            for item in payload.get("workflow_runs", [])
            if item.get("status") in active_statuses
        ]

    def rulesets(self) -> list[dict[str, Any]]:
        summaries = self.api("rulesets?per_page=100")
        return [dict(self.api(f"rulesets/{item['id']}")) for item in summaries]


def _successful_exact_check(checks: Sequence[Mapping[str, Any]], name: str, sha: str) -> bool:
    return any(
        item.get("name") == name
        and item.get("head_sha") == sha
        and item.get("status") == "completed"
        and str(item.get("conclusion", "")).upper() in VALID_CHECK_CONCLUSIONS
        for item in checks
    )


def validate_task_pull_request(
    pull_request: Mapping[str, Any],
    commits: Sequence[Mapping[str, Any]],
    checks: Sequence[Mapping[str, Any]],
    *,
    expected_dev_sha: str,
    require_checks: bool = True,
) -> str:
    base = pull_request.get("base", {})
    head = pull_request.get("head", {})
    if base.get("ref") != "dev":
        raise TaskSessionError("Task pull request base must be dev")
    branch = str(head.get("ref", ""))
    task_id = task_id_from_branch(branch)
    if base.get("sha") != expected_dev_sha:
        raise TaskSessionError(
            f"Task PR is stale: base {base.get('sha')} != current dev {expected_dev_sha}"
        )
    if head.get("repo", {}).get("full_name") != base.get("repo", {}).get("full_name"):
        raise TaskSessionError("Task PR must originate from the same repository")
    title = str(pull_request.get("title", ""))
    if not title.startswith(f"[Task {task_id}]"):
        raise TaskSessionError(f"PR title must start with [Task {task_id}]")
    messages = [str(item.get("commit", {}).get("message", "")) for item in commits]
    declared_commit_count = pull_request.get("commits")
    if declared_commit_count is not None and int(declared_commit_count) != len(commits):
        raise TaskSessionError(
            "Task PR commit inventory is incomplete; split/review the PR instead of truncating provenance"
        )
    validate_task_commit_messages(task_id, messages)
    head_sha = str(head.get("sha", ""))
    if require_checks and not _successful_exact_check(checks, "checks", head_sha):
        raise TaskSessionError(
            f"Exact-head required check 'checks' is not successful for {head_sha}"
        )
    return task_id


def validate_task_pull_request_files(
    files: Sequence[Mapping[str, Any]], *, expected_count: int | None = None
) -> None:
    if expected_count is not None and len(files) != expected_count:
        raise TaskSessionError(
            f"Task PR file inventory is incomplete: received {len(files)} of {expected_count} files"
        )
    forbidden: list[str] = []
    for item in files:
        filename = str(item.get("filename", "")).replace("\\", "/")
        lowered = filename.lower()
        if (
            filename.startswith(".artifacts/")
            or filename.startswith(".git/")
            or (Path(filename).name.startswith(".env") and Path(filename).name != ".env.example")
            or lowered.endswith((".pem", ".key", ".p12", ".pfx"))
        ):
            forbidden.append(filename)
    if forbidden:
        raise TaskSessionError(
            "Task PR contains forbidden artifact/credential paths: " + ", ".join(sorted(forbidden))
        )


def expected_sync_app_id(root: Path) -> int:
    path = root / SYNC_APP_CONFIG_PATH
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        app_id = int(payload["app_id"])
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
        raise TaskSessionError(f"Invalid deployed-sync App config {path}: {error}") from error
    if app_id <= 0:
        raise TaskSessionError(f"Invalid deployed-sync App ID in {path}")
    return app_id


def validate_dev_ruleset(
    rulesets: Sequence[Mapping[str, Any]], *, expected_app_id: int
) -> list[str]:
    matching = [
        item
        for item in rulesets
        if item.get("target") == "branch"
        and item.get("enforcement") == "active"
        and "refs/heads/dev" in item.get("conditions", {}).get("ref_name", {}).get("include", [])
    ]
    if len(matching) != 1:
        return [f"expected exactly one active dev Ruleset, found {len(matching)}"]
    rules = list(matching[0].get("rules", []))
    types = {item.get("type") for item in rules}
    issues = []
    for required in ("deletion", "non_fast_forward", "pull_request", "required_status_checks"):
        if required not in types:
            issues.append(f"dev Ruleset is missing {required}")
    status_rules = [item for item in rules if item.get("type") == "required_status_checks"]
    if status_rules:
        parameters = status_rules[0].get("parameters", {})
        contexts = {item.get("context") for item in parameters.get("required_status_checks", [])}
        if parameters.get("strict_required_status_checks_policy") is not True:
            issues.append("dev Ruleset required checks are not strict-current-base")
        if "checks" not in contexts:
            issues.append("dev Ruleset does not require aggregate checks")
    bypass_actors = list(matching[0].get("bypass_actors", []))
    if len(bypass_actors) != 1:
        issues.append(
            f"dev Ruleset must have exactly one deployed-sync App bypass actor, found {len(bypass_actors)}"
        )
    elif (
        bypass_actors[0].get("actor_type") != "Integration"
        or bypass_actors[0].get("bypass_mode") != "always"
    ):
        issues.append("dev Ruleset bypass must be one Integration actor in always mode")
    elif bypass_actors[0].get("actor_id") != expected_app_id:
        issues.append(
            "dev Ruleset bypass App does not match deployed-sync App: "
            f"expected {expected_app_id}, found {bypass_actors[0].get('actor_id')}"
        )
    return issues


def classify_dev_provenance(
    *,
    sha: str,
    master_sha: str,
    associated_pulls: Sequence[Mapping[str, Any]],
    deploy_runs: Sequence[Mapping[str, Any]],
    approved_recovery_sha: str = "",
) -> dict[str, Any]:
    for pull_request in associated_pulls:
        base = pull_request.get("base", {})
        head = pull_request.get("head", {})
        if (
            pull_request.get("merged_at")
            and pull_request.get("merge_commit_sha") == sha
            and base.get("ref") == "dev"
        ):
            branch = str(head.get("ref", ""))
            task_id = task_id_from_branch(branch)
            title = str(pull_request.get("title", ""))
            if not title.startswith(f"[Task {task_id}]"):
                raise TaskSessionError(f"Merged task PR title does not preserve [Task {task_id}]")
            return {"kind": "task-pr-merge", "task_id": task_id, "pr": pull_request.get("number")}
    if sha == master_sha and any(
        run.get("head_sha") == sha
        and run.get("status") == "completed"
        and run.get("conclusion") == "success"
        and run.get("event") == "workflow_run"
        for run in deploy_runs
    ):
        return {"kind": "deployed-master-sync", "sha": sha}
    if approved_recovery_sha and sha == approved_recovery_sha:
        return {"kind": "owner-approved-recovery", "sha": sha}
    raise TaskSessionError(
        "Unauthorized dev update: expected merged task PR, exact successfully deployed master sync, "
        "or recorded owner-approved recovery SHA"
    )


class TaskController:
    def __init__(
        self,
        repository: GitRepository,
        *,
        github: GitHubClient | None = None,
    ) -> None:
        self.repository = repository
        self.store = StateStore(repository.common_dir)
        self.github = github

    def _github(self) -> GitHubClient:
        if self.github is None:
            self.github = GitHubClient(self.repository)
        return self.github

    def _release_prs(self) -> list[dict[str, Any]]:
        return [
            item
            for item in self._github().open_pull_requests()
            if item.get("base", {}).get("ref") == "master"
            and item.get("head", {}).get("ref") == "dev"
        ]

    def _canonical_root(self) -> Path:
        return self.repository.canonical_dev_worktree().path

    def _completed_dependency_ids(self) -> set[str]:
        roots = (
            self._canonical_root() / "codex-backlog" / "tasks" / "done",
            self._canonical_root() / "codex-backlog" / "bugs" / "done",
            self._canonical_root()
            / "codex-backlog"
            / "telegram-core-release-backlog"
            / "tasks"
            / "done",
        )
        result: set[str] = set()
        for root in roots:
            if root.is_dir():
                for path in root.glob("*.md"):
                    match = TASK_FILE_RE.fullmatch(path.name)
                    if match:
                        result.add(match.group("task_id"))
        return result

    def doctor(self, *, offline: bool = False) -> dict[str, Any]:
        dev = self.repository.canonical_dev_worktree()
        issues: list[str] = []
        dirty = self.repository.status(dev.path)
        if dirty:
            issues.append("main dev worktree is dirty")
        operations = self.repository.operation_issues(dev.path)
        if operations:
            issues.append(f"main dev has active Git operation/lock: {', '.join(operations)}")
        try:
            local_dev = self.repository.ref("dev")
            origin_dev = self.repository.ref("origin/dev")
            origin_master = self.repository.ref("origin/master")
        except TaskSessionError as error:
            issues.append(str(error))
            local_dev = origin_dev = origin_master = "unknown"
        else:
            if local_dev != origin_dev:
                ahead, behind = self.repository.ahead_behind("dev", "origin/dev")
                issues.append(f"local dev differs from origin/dev: ahead={ahead} behind={behind}")
            if not self.repository.is_ancestor("origin/master", "origin/dev"):
                issues.append("origin/dev does not contain origin/master")
        leases: list[dict[str, Any]] = []
        try:
            leases = self.store.all_leases()
        except TaskSessionError as error:
            issues.append(str(error))
        release_prs: list[dict[str, Any]] | str = "offline"
        open_task_prs: list[dict[str, Any]] | str = "offline"
        active_runs: list[dict[str, Any]] | str = "offline"
        rulesets: list[dict[str, Any]] | str = "offline"
        live_dev = "offline"
        if not offline:
            try:
                live_dev = self._github().branch_head("dev")
                if live_dev != origin_dev:
                    issues.append(
                        "local origin/dev is stale: "
                        f"tracking={origin_dev} live={live_dev}; fetch and normalize canonical dev"
                    )
                all_pull_requests = self._github().open_pull_requests()
                release_prs = [
                    {"number": item.get("number"), "title": item.get("title")}
                    for item in all_pull_requests
                    if item.get("base", {}).get("ref") == "master"
                    and item.get("head", {}).get("ref") == "dev"
                ]
                open_task_prs = [
                    {
                        "number": item.get("number"),
                        "title": item.get("title"),
                        "head": item.get("head", {}).get("ref"),
                        "base": item.get("base", {}).get("ref"),
                    }
                    for item in all_pull_requests
                    if str(item.get("head", {}).get("ref", "")).startswith("task/")
                ]
                if release_prs:
                    issues.append("open dev -> master release PR blocks dev mutation")
                active_runs = [
                    {
                        "id": item.get("id"),
                        "name": item.get("name"),
                        "event": item.get("event"),
                        "head_branch": item.get("head_branch"),
                        "head_sha": item.get("head_sha"),
                        "status": item.get("status"),
                    }
                    for item in self._github().active_workflow_runs()
                ]
                rulesets = [
                    {
                        "id": item.get("id"),
                        "name": item.get("name"),
                        "target": item.get("target"),
                        "enforcement": item.get("enforcement"),
                        "conditions": item.get("conditions"),
                        "rules": item.get("rules"),
                        "bypass_actors": item.get("bypass_actors"),
                    }
                    for item in self._github().rulesets()
                ]
                release_critical_runs = [
                    item
                    for item in active_runs
                    if item.get("name") in {"Deploy production", "Sync deployed master to dev"}
                    or item.get("head_branch") in {"dev", "master"}
                ]
                if release_critical_runs:
                    issues.append("active dev/master CI, deploy or sync run blocks mutation")
                issues.extend(
                    validate_dev_ruleset(
                        rulesets,
                        expected_app_id=expected_sync_app_id(self.repository.current_worktree),
                    )
                )
            except TaskSessionError as error:
                issues.append(f"GitHub state unavailable: {error}")
                release_prs = "unavailable"
                open_task_prs = "unavailable"
                active_runs = "unavailable"
                rulesets = "unavailable"
        active_task_ids = {
            item.get("task_id")
            for item in leases
            if item.get("mode") in {"write", "research-readonly"}
        }
        inventory = []
        for worktree in self.repository.worktrees():
            status = self.repository.status(worktree.path)
            unique = (
                self.repository.unique_commits(worktree.branch)
                if worktree.branch and worktree.branch not in {"dev", "master"}
                else self.repository.detached_unique_commits(worktree.path)
                if worktree.detached
                else []
            )
            operation_issues = self.repository.operation_issues(worktree.path)
            upstream = self.repository.upstream(worktree.branch) if worktree.branch else None
            ahead_behind = (
                self.repository.ahead_behind(worktree.branch, upstream)
                if worktree.branch and upstream
                else None
            )
            branch_task_id = None
            if worktree.branch and TASK_BRANCH_RE.fullmatch(worktree.branch):
                branch_task_id = task_id_from_branch(worktree.branch)
            classification = "ACTIVE"
            if branch_task_id in active_task_ids:
                classification = "ACTIVE"
            elif status or operation_issues:
                classification = "DIRTY_NEEDS_OWNER"
            elif (worktree.branch in {"dev", "master"} and ahead_behind != (0, 0)) or (
                worktree.detached and unique
            ):
                classification = "RECOVERY_ANCHOR"
            elif worktree.detached or (worktree.branch not in {"dev", "master"} and not unique):
                classification = "SAFE_TO_REMOVE"
            elif worktree.branch not in {"dev", "master"} and unique:
                classification = "RECOVERY_ANCHOR"
            inventory.append(
                {
                    "path": str(worktree.path),
                    "branch": worktree.branch,
                    "head": worktree.head,
                    "detached": worktree.detached,
                    "dirty": status,
                    "unique_commits_count": len(unique),
                    "unique_commits_preview": unique[:5],
                    "upstream": upstream,
                    "ahead_behind": ahead_behind,
                    "classification": classification,
                    "operation_issues": operation_issues,
                }
            )
        attached_branches = {item.branch for item in self.repository.worktrees() if item.branch}
        local_branches = []
        for branch in self.repository.local_branches():
            name = str(branch["branch"])
            upstream = branch["upstream"]
            unique = self.repository.unique_commits(name)
            classification = "ACTIVE" if name in attached_branches else "UNKNOWN_OWNER"
            if name not in attached_branches and unique:
                classification = "RECOVERY_ANCHOR"
            elif name not in attached_branches and not unique:
                classification = "SAFE_TO_REMOVE"
            local_branches.append(
                {
                    **branch,
                    "ahead_behind": self.repository.ahead_behind(name, str(upstream))
                    if upstream and self.repository.ref_exists(str(upstream))
                    else None,
                    "unique_commits_vs_origin_dev_count": len(unique),
                    "unique_commits_vs_origin_dev_preview": unique[:5],
                    "classification": classification,
                }
            )
        if self.store.lock_path.exists():
            issues.append("coordination state lock exists; recovery is required")
        return {
            "ok": not issues,
            "canonical_dev_worktree": str(dev.path),
            "current_worktree": str(self.repository.current_worktree),
            "git_common_dir": str(self.repository.common_dir),
            "refs": {
                "dev": local_dev,
                "origin/dev": origin_dev,
                "origin/master": origin_master,
                "live/dev": live_dev,
            },
            "leases": leases,
            "release_prs": release_prs,
            "open_task_prs": open_task_prs,
            "active_workflow_runs": active_runs,
            "rulesets": rulesets,
            "inventory": inventory,
            "local_branches": local_branches,
            "issues": issues,
        }

    def status(self) -> dict[str, Any]:
        queue = self.store.read_json(self.store.queue_path, {"version": 1, "candidates": []})
        return {
            "state_root": str(self.store.root),
            "leases": self.store.all_leases(),
            "queue": queue,
        }

    def validate_metadata(self) -> dict[str, Any]:
        roots = (
            self._canonical_root() / "codex-backlog" / "tasks",
            self._canonical_root() / "codex-backlog" / "bugs" / "pending",
            self._canonical_root() / "codex-backlog" / "telegram-core-release-backlog" / "tasks",
        )
        records: list[dict[str, Any]] = []
        errors: list[str] = []
        task_ids: list[str] = []
        for root in roots:
            if not root.is_dir():
                continue
            for path in sorted(root.glob("*.md")):
                match = TASK_FILE_RE.fullmatch(path.name)
                if match is None:
                    continue
                task_id = match.group("task_id")
                task_ids.append(task_id)
                try:
                    document = find_task_document(self._canonical_root(), task_id)
                except TaskSessionError as error:
                    errors.append(str(error))
                    continue
                source_text = document.path.read_text(encoding="utf-8")
                records.append(
                    {
                        "task_id": document.task_id,
                        "canonical_task_path": str(document.path),
                        "dependencies": list(document.dependencies),
                        "executable": document.executable,
                        "concurrency_class": document.concurrency_class,
                        "owner_gate": document.owner_gate,
                        "integration_policy": document.integration_policy,
                        "metadata_source": "task-session-block"
                        if _metadata_block(source_text)
                        else "legacy-inferred",
                    }
                )
        duplicates = sorted({task_id for task_id in task_ids if task_ids.count(task_id) > 1})
        errors.extend(f"Duplicate pending task ID: {task_id}" for task_id in duplicates)
        return {"ok": not errors, "tasks": records, "errors": errors}

    def start(
        self,
        task_id: str,
        *,
        owner_launch: bool,
        session_label: str,
        mode: str = "write",
        slug: str | None = None,
        offline: bool = False,
    ) -> dict[str, Any]:
        expected = normalize_task_id(task_id)
        if not owner_launch:
            raise TaskSessionError("start requires explicit --owner-launch evidence")
        if mode not in {"write", "research-readonly"}:
            raise TaskSessionError(f"Unsupported task lease mode: {mode}")
        report = self.doctor(offline=offline)
        if report["issues"]:
            raise TaskSessionError("doctor blockers: " + "; ".join(report["issues"]))
        document = find_task_document(self._canonical_root(), expected)
        if not document.executable:
            raise TaskSessionError(f"Task {expected} is umbrella/non-executable")
        lowered_status = document.status.lower()
        if "blocked" in lowered_status or "заблок" in lowered_status:
            raise TaskSessionError(f"Task {expected} status is blocked: {document.status}")
        missing = sorted(set(document.dependencies) - self._completed_dependency_ids())
        if missing:
            raise TaskSessionError(
                f"Task {expected} has incomplete dependencies: {', '.join(missing)}"
            )
        if self.store.task_lease_path(expected).exists():
            raise TaskSessionError(f"Task {expected} already has an active lease")
        branch_slug = slug or document.slug
        branch = f"task/{expected}-{branch_slug}"
        task_id_from_branch(branch)
        target = self._canonical_root() / ".artifacts" / "worktrees" / branch.removeprefix("task/")
        if target.exists() or self.repository.ref_exists(f"refs/heads/{branch}"):
            raise TaskSessionError(f"Ambiguous existing branch/worktree for {branch}")
        self.store.initialize()
        lease_path = self.store.task_lease_path(expected)
        with self.store.lock():
            existing = self.store.all_leases()
            if any(item.get("task_id") == expected for item in existing):
                raise TaskSessionError(f"Task {expected} already has an active lease")
            if mode == "write" and any(
                item.get("mode") in {"integration", "release"}
                or (
                    item.get("mode") == "write"
                    and not write_lanes_compatible(
                        document.concurrency_class,
                        str(item.get("concurrency_class", "exclusive-write")),
                    )
                )
                for item in existing
            ):
                raise TaskSessionError("An incompatible write/integration/release lane is occupied")
            if mode == "research-readonly" and any(
                item.get("mode") in {"integration", "release"} for item in existing
            ):
                raise TaskSessionError("Research cannot start during integration/release mutation")
            base_sha = self.repository.ref("origin/dev")
            if not offline:
                live_dev_sha = self._github().branch_head("dev")
                if live_dev_sha != base_sha:
                    raise TaskSessionError(
                        "origin/dev changed while start was acquiring its lease: "
                        f"tracking={base_sha} live={live_dev_sha}"
                    )
            lease = {
                "version": TASK_STATE_VERSION,
                "task_id": expected,
                "canonical_task_path": str(document.path),
                "branch": branch,
                "worktree": str(target.resolve()),
                "base_origin_dev_sha": base_sha,
                "mode": mode,
                "created_at": utc_now(),
                "updated_at": utc_now(),
                "lifecycle_state": "starting",
                "session_label": session_label,
                "concurrency_class": document.concurrency_class,
                "integration_policy": document.integration_policy,
            }
            self.store.create_json(lease_path, lease)
        try:
            self.repository.create_task_worktree(branch, target, base_sha)
        except Exception:
            lease = self.store.read_json(lease_path)
            lease["lifecycle_state"] = "start-failed-recovery-required"
            lease["updated_at"] = utc_now()
            StateStore.replace_json(lease_path, lease)
            raise
        lease["lifecycle_state"] = "implementation"
        lease["updated_at"] = utc_now()
        StateStore.replace_json(lease_path, lease)
        prompt = (
            f"Worktree: {target.resolve()}\n"
            f"Branch: {branch}\nBase origin/dev: {base_sha}\n"
            f"Task: {expected} ({document.path})\n"
            f"Dependencies: {', '.join(document.dependencies) or 'none'}\n"
            f"Concurrency: {document.concurrency_class}; integration: {document.integration_policy}\n"
            "Do not edit the main dev worktree or another worktree. Do not merge, push, release, "
            "or start another task outside this task lifecycle. Approval for a later task is not inherited.\n"
            f"Recovery: python scripts/task_session.py recover {expected}\n"
        )
        return {"lease": lease, "prompt": prompt}

    def adopt_current(
        self, task_id: str, *, owner_launch: bool, session_label: str
    ) -> dict[str, Any]:
        expected = normalize_task_id(task_id)
        if not owner_launch:
            raise TaskSessionError("adopt-current requires explicit --owner-launch evidence")
        branch = self.repository.git("branch", "--show-current")
        if not branch or task_id_from_branch(branch) != expected:
            raise TaskSessionError(f"Current branch {branch!r} does not match Task {expected}")
        if self.repository.current_worktree == self._canonical_root():
            raise TaskSessionError("Cannot adopt the main integration-only dev worktree")
        matching_worktrees = [
            item
            for item in self.repository.worktrees()
            if item.branch and item.branch.startswith(f"task/{expected}-")
        ]
        if len(matching_worktrees) != 1:
            raise TaskSessionError(
                f"Expected exactly one existing Task {expected} worktree, found {len(matching_worktrees)}"
            )
        head_sha = self.repository.ref("HEAD")
        origin_dev_sha = self.repository.ref("origin/dev")
        if head_sha != origin_dev_sha and not self.repository.is_ancestor(origin_dev_sha, head_sha):
            raise TaskSessionError("Existing task branch is not based on current origin/dev")
        if self._release_prs():
            raise TaskSessionError("Open dev -> master release PR blocks adoption")
        document = find_task_document(self._canonical_root(), expected)
        self.store.initialize()
        lease_path = self.store.task_lease_path(expected)
        lease = {
            "version": TASK_STATE_VERSION,
            "task_id": expected,
            "canonical_task_path": str(document.path),
            "branch": branch,
            "worktree": str(self.repository.current_worktree),
            "base_origin_dev_sha": origin_dev_sha,
            "mode": "write",
            "created_at": utc_now(),
            "updated_at": utc_now(),
            "lifecycle_state": "implementation",
            "session_label": session_label,
            "concurrency_class": document.concurrency_class,
            "integration_policy": document.integration_policy,
            "adopted_existing_session": True,
        }
        with self.store.lock():
            existing = self.store.all_leases()
            if any(
                item.get("mode") in {"integration", "release"}
                or (
                    item.get("mode") == "write"
                    and not write_lanes_compatible(
                        document.concurrency_class,
                        str(item.get("concurrency_class", "exclusive-write")),
                    )
                )
                for item in existing
            ):
                raise TaskSessionError("An incompatible write/integration/release lane is occupied")
            self.store.create_json(lease_path, lease)
        return lease

    def mark_ready(
        self,
        task_id: str,
        *,
        head_sha: str,
        review_verdict: str,
        qa_verdict: str,
    ) -> dict[str, Any]:
        expected = normalize_task_id(task_id)
        if review_verdict not in {"APPROVED", "APPROVED_WITH_NON_BLOCKING_FINDINGS"}:
            raise TaskSessionError("mark-ready requires an approved independent review verdict")
        if qa_verdict != "PASS":
            raise TaskSessionError("mark-ready requires QA verdict PASS")
        lease_path = self.store.task_lease_path(expected)
        lease = self.store.read_json(lease_path)
        if lease is None or lease.get("mode") != "write":
            raise TaskSessionError("Only an active write lease can become integration-ready")
        if lease.get("lifecycle_state") not in {"implementation", "ready-integration"}:
            raise TaskSessionError(
                f"Task {expected} cannot become ready from {lease.get('lifecycle_state')}"
            )
        worktree = Path(str(lease["worktree"]))
        if self.repository.status(worktree):
            raise TaskSessionError("Task worktree must be clean before integration readiness")
        actual_branch = self.repository.git("branch", "--show-current", cwd=worktree)
        if actual_branch != lease.get("branch") or task_id_from_branch(actual_branch) != expected:
            raise TaskSessionError("Task worktree branch does not match its lease")
        actual_head = self.repository.git("rev-parse", "HEAD", cwd=worktree)
        if actual_head != head_sha:
            raise TaskSessionError(f"Task HEAD {actual_head} != declared ready SHA {head_sha}")
        base_sha = str(lease["base_origin_dev_sha"])
        if not self.repository.is_ancestor(base_sha, head_sha):
            raise TaskSessionError("Task HEAD does not descend from leased origin/dev base")
        validate_task_commit_messages(expected, self.repository.commits(f"{base_sha}..{head_sha}"))
        with self.store.lock():
            current = self.store.read_json(lease_path)
            if current.get("updated_at") != lease.get("updated_at"):
                raise TaskSessionError("Task lease changed while readiness was validated")
            if current.get("lifecycle_state") == "ready-integration":
                queue = self.store.read_json(
                    self.store.queue_path, {"version": 1, "candidates": []}
                )
                if any(item.get("task_id") == expected for item in queue["candidates"]):
                    raise TaskSessionError(
                        "Queued task readiness is immutable; remove it only through explicit recovery"
                    )
                if self.store.mode_lease_path("integration").exists():
                    raise TaskSessionError("Integration lease blocks task readiness replacement")
            current["lifecycle_state"] = "ready-integration"
            current["ready_head_sha"] = head_sha
            current["review_verdict"] = review_verdict
            current["qa_verdict"] = qa_verdict
            current["updated_at"] = utc_now()
            StateStore.replace_json(lease_path, current)
        return current

    def recover(self, task_id: str) -> dict[str, Any]:
        expected = normalize_task_id(task_id)
        lease = self.store.read_json(self.store.task_lease_path(expected))
        worktrees = self.repository.worktrees()
        matches = [
            item
            for item in worktrees
            if (lease and str(item.path) == lease.get("worktree"))
            or (item.branch and item.branch.startswith(f"task/{expected}-"))
        ]
        branches = [
            line.removeprefix("refs/heads/")
            for line in self.repository.git(
                "for-each-ref", "--format=%(refname)", f"refs/heads/task/{expected}-*"
            ).splitlines()
            if line
        ]
        details = []
        for worktree in matches:
            details.append(
                {
                    **asdict(worktree),
                    "path": str(worktree.path),
                    "dirty": self.repository.status(worktree.path),
                    "operation_issues": self.repository.operation_issues(worktree.path),
                    "unique_commits": self.repository.unique_commits(worktree.branch)
                    if worktree.branch
                    else [],
                }
            )
        issues: list[str] = []
        if lease is None:
            issues.append("missing task lease")
        if len(branches) > 1 or len(matches) > 1:
            issues.append("duplicate task branch/worktree")
        if lease and not matches:
            issues.append("lease exists but worktree is missing")
        if any(item["dirty"] or item["operation_issues"] for item in details):
            issues.append("dirty or interrupted worktree requires owner-safe recovery")
        if any(item["unique_commits"] for item in details):
            issues.append("unique commits make automatic cleanup unsafe")
        return {
            "task_id": expected,
            "lease": lease,
            "branches": branches,
            "worktrees": details,
            "classification": "RECOVERY_REQUIRED" if issues else "CONSISTENT",
            "issues": issues,
            "mutation_performed": False,
        }

    def enqueue_integration(self, task_id: str, *, pr_number: int) -> dict[str, Any]:
        expected = normalize_task_id(task_id)
        self.store.initialize()
        lease = self.store.read_json(self.store.task_lease_path(expected))
        if lease is None:
            raise TaskSessionError(f"Task {expected} has no active lease")
        if lease.get("mode") != "write":
            raise TaskSessionError("Research-readonly lease cannot enter integration queue")
        if lease.get("lifecycle_state") != "ready-integration":
            raise TaskSessionError("Task must pass mark-ready before integration queue")
        if self.store.mode_lease_path("release").exists() or self._release_prs():
            raise TaskSessionError("Release freeze blocks integration queue mutation")
        pull_request = self._github().pull_request(pr_number)
        commits = self._github().pull_request_commits(pr_number)
        files = self._github().pull_request_files(pr_number)
        checks = self._github().check_runs(str(pull_request["head"]["sha"]))
        actual = validate_task_pull_request(
            pull_request,
            commits,
            checks,
            expected_dev_sha=self._github().branch_head("dev"),
            require_checks=False,
        )
        if actual != expected:
            raise TaskSessionError(f"PR task ID {actual} does not match lease {expected}")
        if pull_request["head"]["sha"] != lease.get("ready_head_sha"):
            raise TaskSessionError("PR head does not match the review/QA-ready task SHA")
        validate_task_pull_request_files(
            files, expected_count=int(pull_request.get("changed_files", len(files)))
        )
        with self.store.lock():
            queue = self.store.read_json(self.store.queue_path, {"version": 1, "candidates": []})
            if any(item["task_id"] == expected for item in queue["candidates"]):
                raise TaskSessionError(f"Task {expected} is already queued")
            queue["candidates"].append(
                {
                    "task_id": expected,
                    "pr_number": pr_number,
                    "head_sha": pull_request["head"]["sha"],
                    "base_sha": pull_request["base"]["sha"],
                    "state": "queued",
                    "queued_at": utc_now(),
                }
            )
            StateStore.replace_json(self.store.queue_path, queue)
        return queue

    def prepare_integration(self, task_id: str) -> dict[str, Any]:
        expected = normalize_task_id(task_id)
        if self.store.mode_lease_path("release").exists() or self._release_prs():
            raise TaskSessionError("Release freeze blocks integration")
        queue = self.store.read_json(self.store.queue_path, {"version": 1, "candidates": []})
        candidates = queue["candidates"]
        if not candidates or candidates[0]["task_id"] != expected:
            head = candidates[0]["task_id"] if candidates else "<empty>"
            raise TaskSessionError(f"Only queue head may integrate; current head is {head}")
        candidate = candidates[0]
        pull_request = self._github().pull_request(int(candidate["pr_number"]))
        commits = self._github().pull_request_commits(int(candidate["pr_number"]))
        files = self._github().pull_request_files(int(candidate["pr_number"]))
        head_sha = str(pull_request["head"]["sha"])
        checks = self._github().check_runs(head_sha)
        task_id_from_pr = validate_task_pull_request(
            pull_request,
            commits,
            checks,
            expected_dev_sha=self._github().branch_head("dev"),
            require_checks=True,
        )
        if task_id_from_pr != expected or head_sha != candidate["head_sha"]:
            raise TaskSessionError("Queued candidate changed; enqueue fresh exact-head evidence")
        validate_task_pull_request_files(
            files, expected_count=int(pull_request.get("changed_files", len(files)))
        )
        integration_lease = {
            "version": 1,
            "task_id": expected,
            "canonical_task_path": self.store.read_json(self.store.task_lease_path(expected))[
                "canonical_task_path"
            ],
            "branch": pull_request["head"]["ref"],
            "worktree": self.store.read_json(self.store.task_lease_path(expected))["worktree"],
            "base_origin_dev_sha": pull_request["base"]["sha"],
            "mode": "integration",
            "created_at": utc_now(),
            "updated_at": utc_now(),
            "lifecycle_state": "eligible-exact-head",
            "session_label": f"pr-{candidate['pr_number']}",
            "pr_number": candidate["pr_number"],
            "head_sha": head_sha,
        }
        with self.store.lock():
            if self.store.mode_lease_path("release").exists():
                raise TaskSessionError("Release freeze acquired while integration was validated")
            current_queue = self.store.read_json(
                self.store.queue_path, {"version": 1, "candidates": []}
            )
            if (
                not current_queue["candidates"]
                or current_queue["candidates"][0].get("task_id") != expected
                or current_queue["candidates"][0].get("head_sha") != head_sha
                or current_queue["candidates"][0].get("state") != "queued"
            ):
                raise TaskSessionError(
                    "Integration queue head changed while eligibility was validated"
                )
            self.store.create_json(self.store.mode_lease_path("integration"), integration_lease)
            current_queue["candidates"][0]["state"] = "eligible"
            current_queue["candidates"][0]["eligible_at"] = utc_now()
            StateStore.replace_json(self.store.queue_path, current_queue)
        return integration_lease

    def withdraw_integration(self, task_id: str, *, reason: str) -> dict[str, Any]:
        expected = normalize_task_id(task_id)
        if not reason.strip():
            raise TaskSessionError("withdraw-integration requires a non-empty reason")
        integration_path = self.store.mode_lease_path("integration")
        integration = self.store.read_json(integration_path)
        if integration is None or integration.get("task_id") != expected:
            raise TaskSessionError(f"Task {expected} does not own integration lease")
        pull_request = self._github().pull_request(int(integration["pr_number"]))
        if pull_request.get("merged_at"):
            raise TaskSessionError("Merged integration cannot be withdrawn; verify exact dev CI")
        with self.store.lock():
            current = self.store.read_json(integration_path)
            if current != integration:
                raise TaskSessionError("Integration lease changed while withdrawal was validated")
            queue = self.store.read_json(self.store.queue_path)
            if (
                not queue["candidates"]
                or queue["candidates"][0].get("task_id") != expected
                or queue["candidates"][0].get("head_sha") != integration.get("head_sha")
            ):
                raise TaskSessionError("Integration queue head changed before withdrawal")
            withdrawn = queue["candidates"].pop(0)
            withdrawn.update(
                {
                    "state": "withdrawn-for-fix",
                    "withdrawn_at": utc_now(),
                    "reason": reason.strip(),
                }
            )
            task_lease_path = self.store.task_lease_path(expected)
            task_lease = self.store.read_json(task_lease_path)
            if task_lease is None:
                raise TaskSessionError("Task lease is missing during integration withdrawal")
            task_lease["lifecycle_state"] = "implementation"
            task_lease["updated_at"] = utc_now()
            task_lease["last_integration_withdrawal"] = withdrawn
            for field in ("ready_head_sha", "review_verdict", "qa_verdict"):
                task_lease.pop(field, None)
            StateStore.replace_json(self.store.queue_path, queue)
            StateStore.replace_json(task_lease_path, task_lease)
            integration_path.unlink()
        return {"withdrawn": withdrawn, "task_lease": task_lease}

    def complete_integration(self, task_id: str, *, merge_sha: str) -> dict[str, Any]:
        expected = normalize_task_id(task_id)
        integration_path = self.store.mode_lease_path("integration")
        integration = self.store.read_json(integration_path)
        if integration is None or integration.get("task_id") != expected:
            raise TaskSessionError(f"Task {expected} does not own integration lease")
        dev_head = self._github().branch_head("dev")
        if dev_head != merge_sha:
            raise TaskSessionError(f"origin/dev {dev_head} != expected merge SHA {merge_sha}")
        pull_request = self._github().pull_request(int(integration["pr_number"]))
        if (
            not pull_request.get("merged_at")
            or pull_request.get("merge_commit_sha") != merge_sha
            or pull_request.get("head", {}).get("sha") != integration.get("head_sha")
            or pull_request.get("base", {}).get("ref") != "dev"
        ):
            raise TaskSessionError(
                "Current dev SHA is not the exact merge result of the leased task PR/head"
            )
        runs = self._github().workflow_runs("ci.yml", merge_sha)
        successful = [
            run
            for run in runs
            if run.get("event") == "push"
            and run.get("head_branch") == "dev"
            and run.get("head_sha") == merge_sha
            and run.get("status") == "completed"
            and run.get("conclusion") == "success"
        ]
        if not successful:
            raise TaskSessionError(f"No terminal successful exact-SHA dev push CI for {merge_sha}")
        with self.store.lock():
            queue = self.store.read_json(self.store.queue_path)
            if not queue["candidates"] or queue["candidates"][0]["task_id"] != expected:
                raise TaskSessionError("Integration queue head changed unexpectedly")
            completed = queue["candidates"].pop(0)
            completed.update(
                {
                    "state": "dev-ci-success",
                    "merge_sha": merge_sha,
                    "dev_ci_run_id": successful[0].get("id"),
                    "completed_at": utc_now(),
                }
            )
            StateStore.replace_json(self.store.queue_path, queue)
            history_path = self.store.history / f"task-{expected}.json"
            self.store.create_json(history_path, completed)
            integration_path.unlink()
            task_lease_path = self.store.task_lease_path(expected)
            task_lease = self.store.read_json(task_lease_path)
            task_lease["lifecycle_state"] = "dev-ci-success"
            task_lease["updated_at"] = utc_now()
            task_lease["merge_sha"] = merge_sha
            task_lease["dev_ci_run_id"] = successful[0].get("id")
            StateStore.replace_json(task_lease_path, task_lease)
        return completed

    def finish(self, task_id: str) -> dict[str, Any]:
        expected = normalize_task_id(task_id)
        lease_path = self.store.task_lease_path(expected)
        lease = self.store.read_json(lease_path)
        history_path = self.store.history / f"task-{expected}.json"
        history = self.store.read_json(history_path)
        if lease is None or history is None:
            raise TaskSessionError("finish requires task lease and completed integration history")
        if lease.get("lifecycle_state") != "dev-ci-success":
            raise TaskSessionError("finish requires terminal dev-ci-success state")
        recovery = self.recover(expected)
        cleanup_allowed = not any(
            item["dirty"] or item["operation_issues"] or item["unique_commits"]
            for item in recovery["worktrees"]
        )
        with self.store.lock():
            history["state"] = "finished"
            history["finished_at"] = utc_now()
            history["cleanup_allowed_after_owner_confirmation"] = cleanup_allowed
            StateStore.replace_json(history_path, history)
            lease_path.unlink()
        return {
            "history": history,
            "cleanup_performed": False,
            "cleanup_allowed_after_owner_confirmation": cleanup_allowed,
        }

    def release_freeze(self, action: str, *, sha: str, session_label: str) -> dict[str, Any]:
        path = self.store.mode_lease_path("release")
        self.store.initialize()
        if action == "start":
            payload = {
                "version": 1,
                "task_id": "release",
                "canonical_task_path": "release-lifecycle",
                "branch": "dev",
                "worktree": str(self._canonical_root()),
                "base_origin_dev_sha": sha,
                "mode": "release",
                "created_at": utc_now(),
                "updated_at": utc_now(),
                "lifecycle_state": "release-freeze",
                "session_label": session_label,
            }
            with self.store.lock():
                if self.store.mode_lease_path("integration").exists():
                    raise TaskSessionError("Cannot start release while integration lease is active")
                self.store.create_json(path, payload)
            return payload
        if action != "finish":
            raise TaskSessionError(f"Unknown release-freeze action: {action}")
        payload = self.store.read_json(path)
        if payload is None:
            raise TaskSessionError("No active release lease")
        if payload.get("base_origin_dev_sha") != sha:
            raise TaskSessionError("Release finish SHA does not match lease")
        with self.store.lock():
            path.unlink()
        return {"released": True, "sha": sha}


def verify_dev_provenance(
    repository: GitRepository,
    github: GitHubClient,
    *,
    sha: str,
    approved_recovery_sha: str,
) -> dict[str, Any]:
    associated = github.api(f"commits/{sha}/pulls")
    master_sha = github.branch_head("master")
    deploy_runs = github.workflow_runs("deploy.yml", sha)
    return classify_dev_provenance(
        sha=sha,
        master_sha=master_sha,
        associated_pulls=associated,
        deploy_runs=deploy_runs,
        approved_recovery_sha=approved_recovery_sha,
    )


def validate_pr_event(
    repository: GitRepository, github: GitHubClient, event_path: Path
) -> dict[str, Any]:
    event = json.loads(event_path.read_text(encoding="utf-8"))
    pull_request = event.get("pull_request")
    if not isinstance(pull_request, dict):
        return {"kind": "not-pull-request"}
    base_ref = pull_request.get("base", {}).get("ref")
    if base_ref == "master":
        head_ref = str(pull_request.get("head", {}).get("ref", ""))
        if head_ref == "dev":
            return {"kind": "release-pr", "head_sha": pull_request["head"]["sha"]}
        if head_ref.startswith(("hotfix/", "recovery/")) and str(
            pull_request.get("title", "")
        ).startswith("[Recovery approved]"):
            return {
                "kind": "owner-approved-exceptional-pr",
                "head_ref": head_ref,
                "head_sha": pull_request["head"]["sha"],
            }
        raise TaskSessionError(
            "Normal release PR into master must have head dev; exceptional hotfix/recovery "
            "requires an owner-approved branch and [Recovery approved] title"
        )
    if base_ref != "dev":
        raise TaskSessionError(f"Unsupported pull request base: {base_ref}")
    number = int(pull_request["number"])
    commits = github.pull_request_commits(number)
    files = github.pull_request_files(number)
    task_id = validate_task_pull_request(
        pull_request,
        commits,
        [],
        expected_dev_sha=str(pull_request["base"]["sha"]),
        require_checks=False,
    )
    validate_task_pull_request_files(
        files, expected_count=int(pull_request.get("changed_files", len(files)))
    )
    return {"kind": "task-pr", "task_id": task_id, "head_sha": pull_request["head"]["sha"]}


def archive_guard(backlog_root: Path, task_id: str) -> None:
    """Require controller finalization when the new contract is active locally."""

    repository_root = next(
        (
            candidate
            for candidate in (backlog_root.resolve(), *backlog_root.resolve().parents)
            if (candidate / ".git").exists()
        ),
        None,
    )
    if repository_root is None:
        return
    git_marker = repository_root / ".git"
    if git_marker.is_dir() and not (git_marker / STATE_DIRECTORY_NAME / "contract.json").exists():
        return
    repository = GitRepository(backlog_root)
    store = StateStore(repository.common_dir)
    if not (store.root / "contract.json").exists():
        return
    history = store.read_json(store.history / f"task-{normalize_task_id(task_id)}.json")
    if history is None or history.get("state") != "finished":
        raise TaskSessionError(
            f"Task {task_id} cannot be archived before controller finish and terminal dev CI"
        )


def _print(payload: Mapping[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--github-repository")
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor = subparsers.add_parser("doctor")
    doctor.add_argument("--offline", action="store_true")

    subparsers.add_parser("status")
    subparsers.add_parser("validate-metadata")

    start = subparsers.add_parser("start")
    start.add_argument("task_id")
    start.add_argument("--owner-launch", action="store_true")
    start.add_argument("--session-label", required=True)
    start.add_argument("--mode", choices=("write", "research-readonly"), default="write")
    start.add_argument("--slug")
    start.add_argument("--offline", action="store_true")

    adopt = subparsers.add_parser("adopt-current")
    adopt.add_argument("task_id")
    adopt.add_argument("--owner-launch", action="store_true")
    adopt.add_argument("--session-label", required=True)

    ready = subparsers.add_parser("mark-ready")
    ready.add_argument("task_id")
    ready.add_argument("--head-sha", required=True)
    ready.add_argument(
        "--review-verdict",
        choices=("APPROVED", "APPROVED_WITH_NON_BLOCKING_FINDINGS"),
        required=True,
    )
    ready.add_argument("--qa-verdict", choices=("PASS",), required=True)

    recover = subparsers.add_parser("recover")
    recover.add_argument("task_id")

    enqueue = subparsers.add_parser("enqueue-integration")
    enqueue.add_argument("task_id")
    enqueue.add_argument("--pr", type=int, required=True)

    prepare = subparsers.add_parser("prepare-integration")
    prepare.add_argument("task_id")

    withdraw = subparsers.add_parser("withdraw-integration")
    withdraw.add_argument("task_id")
    withdraw.add_argument("--reason", required=True)

    complete = subparsers.add_parser("complete-integration")
    complete.add_argument("task_id")
    complete.add_argument("--merge-sha", required=True)

    finish = subparsers.add_parser("finish")
    finish.add_argument("task_id")

    freeze = subparsers.add_parser("release-freeze")
    freeze.add_argument("action", choices=("start", "finish"))
    freeze.add_argument("--sha", required=True)
    freeze.add_argument("--session-label", default="integration-release")

    validate_pr = subparsers.add_parser("validate-pr")
    validate_pr.add_argument("--event", type=Path, required=True)

    provenance = subparsers.add_parser("verify-dev-provenance")
    provenance.add_argument("--sha", required=True)
    provenance.add_argument("--approved-recovery-sha", default="")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        repository = GitRepository(args.repo)
        github = GitHubClient(repository, args.github_repository)
        controller = TaskController(repository, github=github)
        if args.command == "doctor":
            payload = controller.doctor(offline=args.offline)
            _print(payload)
            return 0 if payload["ok"] else 1
        if args.command == "status":
            _print(controller.status())
            return 0
        if args.command == "validate-metadata":
            payload = controller.validate_metadata()
            _print(payload)
            return 0 if payload["ok"] else 1
        if args.command == "start":
            _print(
                controller.start(
                    args.task_id,
                    owner_launch=args.owner_launch,
                    session_label=args.session_label,
                    mode=args.mode,
                    slug=args.slug,
                    offline=args.offline,
                )
            )
            return 0
        if args.command == "adopt-current":
            _print(
                controller.adopt_current(
                    args.task_id,
                    owner_launch=args.owner_launch,
                    session_label=args.session_label,
                )
            )
            return 0
        if args.command == "mark-ready":
            _print(
                controller.mark_ready(
                    args.task_id,
                    head_sha=args.head_sha,
                    review_verdict=args.review_verdict,
                    qa_verdict=args.qa_verdict,
                )
            )
            return 0
        if args.command == "recover":
            _print(controller.recover(args.task_id))
            return 0
        if args.command == "enqueue-integration":
            _print(controller.enqueue_integration(args.task_id, pr_number=args.pr))
            return 0
        if args.command == "prepare-integration":
            _print(controller.prepare_integration(args.task_id))
            return 0
        if args.command == "withdraw-integration":
            _print(controller.withdraw_integration(args.task_id, reason=args.reason))
            return 0
        if args.command == "complete-integration":
            _print(controller.complete_integration(args.task_id, merge_sha=args.merge_sha))
            return 0
        if args.command == "finish":
            _print(controller.finish(args.task_id))
            return 0
        if args.command == "release-freeze":
            _print(
                controller.release_freeze(
                    args.action, sha=args.sha, session_label=args.session_label
                )
            )
            return 0
        if args.command == "validate-pr":
            _print(validate_pr_event(repository, github, args.event))
            return 0
        if args.command == "verify-dev-provenance":
            _print(
                verify_dev_provenance(
                    repository,
                    github,
                    sha=args.sha,
                    approved_recovery_sha=args.approved_recovery_sha,
                )
            )
            return 0
        raise AssertionError(f"Unhandled command: {args.command}")
    except (TaskSessionError, OSError, json.JSONDecodeError) as error:
        print(f"task session error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
