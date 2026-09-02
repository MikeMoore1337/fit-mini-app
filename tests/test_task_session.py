from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any

import pytest


def _load_module():
    script = Path(__file__).parents[1] / "scripts" / "task_session.py"
    spec = importlib.util.spec_from_file_location("task_session", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


task_session = _load_module()


def _git(path: Path, *args: str) -> str:
    completed = subprocess.run(["git", *args], cwd=path, check=True, text=True, capture_output=True)
    return completed.stdout.strip()


def _write_task(root: Path, task_id: str, slug: str, *, dependencies: str = "") -> Path:
    tasks = root / "codex-backlog" / "tasks"
    tasks.mkdir(parents=True, exist_ok=True)
    path = tasks / f"{task_id}-{slug}.md"
    path.write_text(
        "# Task fixture\n\n"
        "- **Статус:** owner-selected, not started\n"
        "- **Тип:** implementation\n"
        "<!-- task-session\n"
        f"dependencies: {dependencies}\n"
        "executable: true\n"
        "concurrency: exclusive-write\n"
        "owner_gate: explicit-launch\n"
        "integration: task-pr-to-master\n"
        "-->\n",
        encoding="utf-8",
    )
    return path


@pytest.fixture
def repository(tmp_path: Path):
    test_root = Path(__file__).parents[1] / ".artifacts" / f"task-session-{uuid.uuid4().hex[:8]}"
    root = test_root / "repository with spaces"
    remote = test_root / "remote.git"
    test_root.mkdir(parents=True)
    root.mkdir()
    _git(root, "init", "-b", "master")
    _git(root, "config", "user.name", "Task Session Tests")
    _git(root, "config", "user.email", "task-session@example.invalid")
    (root / ".gitignore").write_text("/codex-backlog/tasks/\n.artifacts/\n", encoding="utf-8")
    (root / "README.md").write_text("initial\n", encoding="utf-8")
    _git(root, "add", ".gitignore", "README.md")
    _git(root, "commit", "-m", "chore: initial")
    _git(test_root, "init", "--bare", str(remote))
    _git(root, "remote", "add", "origin", str(remote))
    _git(root, "push", "-u", "origin", "master")
    _git(root, "fetch", "origin")
    repository = task_session.GitRepository(root)
    try:
        yield root, repository
    finally:
        for worktree in repository.worktrees():
            if worktree.path != root:
                _git(root, "worktree", "remove", "--force", str(worktree.path))
        _git(root, "worktree", "prune")
        shutil.rmtree(test_root, ignore_errors=True)


class FakeGitHub:
    def __init__(self, master_sha: str) -> None:
        self.master_sha = master_sha
        self.pulls: dict[int, dict[str, Any]] = {}
        self.commits: dict[int, list[dict[str, Any]]] = {}
        self.files: dict[int, list[dict[str, Any]]] = {}
        self.checks: dict[str, list[dict[str, Any]]] = {}
        self.open_prs: list[dict[str, Any]] = []
        self.active_runs: list[dict[str, Any]] = []
        self.ruleset_payload: list[dict[str, Any]] = []
        self.successful_deployments: set[tuple[str, str]] = set()
        self.associated_pulls: list[dict[str, Any]] = []

    def api(self, endpoint: str) -> Any:
        if endpoint.startswith("commits/") and endpoint.endswith("/pulls"):
            return self.associated_pulls
        raise AssertionError(f"Unexpected fake GitHub API endpoint: {endpoint}")

    def open_pull_requests(self) -> list[dict[str, Any]]:
        return self.open_prs

    def pull_request(self, number: int) -> dict[str, Any]:
        return self.pulls[number]

    def pull_request_commits(self, number: int) -> list[dict[str, Any]]:
        return self.commits[number]

    def pull_request_files(self, number: int) -> list[dict[str, Any]]:
        return self.files.get(number, [{"filename": "README.md"}])

    def check_runs(self, sha: str) -> list[dict[str, Any]]:
        return self.checks.get(sha, [])

    def branch_head(self, branch: str) -> str:
        if branch != "master":
            raise AssertionError(f"Unexpected branch lookup: {branch}")
        return self.master_sha

    def has_successful_deployment(self, sha: str, environment: str) -> bool:
        return (sha, environment) in self.successful_deployments

    def active_workflow_runs(self) -> list[dict[str, Any]]:
        return self.active_runs

    def rulesets(self) -> list[dict[str, Any]]:
        return self.ruleset_payload


def _task_pr(
    number: int,
    task_id: str,
    base_sha: str,
    head_sha: str,
    *,
    base_branch: str = "master",
    merge_sha: str | None = None,
) -> dict[str, Any]:
    return {
        "number": number,
        "title": f"[Task {task_id}] Synthetic task",
        "merged_at": "2026-09-03T10:00:00Z" if merge_sha else None,
        "merge_commit_sha": merge_sha,
        "commits": 1,
        "changed_files": 1,
        "base": {
            "ref": base_branch,
            "sha": base_sha,
            "repo": {"full_name": "owner/repository"},
        },
        "head": {
            "ref": f"task/{task_id}-synthetic-task",
            "sha": head_sha,
            "repo": {"full_name": "owner/repository"},
        },
    }


def _task_commit(task_id: str) -> dict[str, Any]:
    return {"commit": {"message": f"feat: [Task {task_id}] synthetic change"}}


def _success_check(sha: str) -> dict[str, Any]:
    return {"name": "checks", "head_sha": sha, "status": "completed", "conclusion": "SUCCESS"}


def _prepare_started(
    repository: tuple[Path, Any], task_id: str = "301"
) -> tuple[Path, Any, Any, Path, str, str]:
    root, git_repository = repository
    _write_task(root, task_id, "synthetic-task")
    controller = task_session.TaskController(
        git_repository, github=FakeGitHub(git_repository.ref("origin/master"))
    )
    started = controller.start(task_id, owner_launch=True, session_label="pytest", offline=True)
    worktree = Path(started["lease"]["worktree"])
    branch = str(started["lease"]["branch"])
    base_sha = str(started["lease"]["base_origin_master_sha"])
    (worktree / "change.txt").write_text("change\n", encoding="utf-8")
    _git(worktree, "add", "change.txt")
    _git(worktree, "commit", "-m", f"feat: [Task {task_id}] synthetic change")
    head_sha = _git(worktree, "rev-parse", "HEAD")
    return root, git_repository, controller, worktree, branch, base_sha + ":" + head_sha


def _write_gate_evidence(
    controller: Any,
    task_id: str,
    *,
    branch: str,
    head_sha: str,
    base_sha: str,
    terminal_result: str = "PRE_PUSH_CI_PASS",
) -> Path:
    from scripts.ci_contract import contract_digest
    from scripts.pre_push_gate import _evidence_digest

    path = controller._gate_evidence_path(controller._canonical_root(), task_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "evidence_version": 1,
        "contract_version": "ci-contract-v1",
        "contract_digest": contract_digest(),
        "task_id": task_id,
        "branch": branch,
        "head_sha": head_sha,
        "base_sha": base_sha,
        "target_base_branch": "master",
        "clean_worktree": True,
        "started_at": "2026-09-03T10:00:00Z",
        "finished_at": "2026-09-03T10:01:00Z",
        "gates": [{"group": "quality", "applicable": True, "status": "SUCCESS"}],
        "terminal_result": terminal_result,
    }
    payload["evidence_digest"] = _evidence_digest(payload)
    path.write_text(
        json.dumps(payload),
        encoding="utf-8",
    )
    return path


def test_run_scopes_git_safety_to_exact_worktree(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    observed: dict[str, Any] = {}

    def fake_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        observed["args"] = args[0]
        return subprocess.CompletedProcess(args[0], 0, stdout="", stderr="")

    monkeypatch.setattr(task_session.subprocess, "run", fake_run)
    task_session._run(["git", "status", "--short"], cwd=tmp_path)
    command = observed["args"]
    assert command[:3] == ["git", "-c", f"safe.directory={tmp_path.resolve().as_posix()}"]
    if task_session.os.name == "nt":
        assert command[3:5] == ["-c", "core.longpaths=true"]


@pytest.mark.parametrize("task_id", ["127", "90A", "124C"])
def test_task_ids_and_branch_traceability_accept_suffix_ids(task_id: str) -> None:
    task_session.validate_task_commit_messages(task_id, [f"fix: [Task {task_id}] preserve trace"])
    assert task_session.task_id_from_branch(f"task/{task_id}-valid-kebab") == task_id


@pytest.mark.parametrize(
    "branch", ["feature/127-x", "task/127", "task/127-Bad-Slug", "task/127_bad", "task/A127-test"]
)
def test_invalid_task_branch_names_fail_closed(branch: str) -> None:
    with pytest.raises(task_session.TaskSessionError, match="must match"):
        task_session.task_id_from_branch(branch)


def test_task_pr_requires_master_and_exact_head_check() -> None:
    base_sha = "a" * 40
    head_sha = "b" * 40
    pull_request = _task_pr(135, "135", base_sha, head_sha)
    assert (
        task_session.validate_task_pull_request(
            pull_request,
            [_task_commit("135")],
            [_success_check(head_sha)],
            expected_base_sha=base_sha,
        )
        == "135"
    )

    pull_request["base"]["ref"] = "dev"
    with pytest.raises(task_session.TaskSessionError, match="base must be master"):
        task_session.validate_task_pull_request(
            pull_request,
            [_task_commit("135")],
            [_success_check(head_sha)],
            expected_base_sha=base_sha,
        )


def test_validate_pr_event_rejects_base_behind_live_master(
    tmp_path: Path,
) -> None:
    base_sha = "a" * 40
    live_master_sha = "c" * 40
    head_sha = "b" * 40
    event_path = tmp_path / "event.json"
    event_path.write_text(
        json.dumps({"pull_request": _task_pr(135, "135", base_sha, head_sha)}),
        encoding="utf-8",
    )
    github = FakeGitHub(live_master_sha)
    github.commits[135] = [_task_commit("135")]
    with pytest.raises(task_session.TaskSessionError, match="Task PR is stale"):
        task_session.validate_pr_event(object(), github, event_path)  # type: ignore[arg-type]


def test_master_ruleset_requires_pr_current_base_and_aggregate_check() -> None:
    weak = [
        {
            "target": "branch",
            "enforcement": "active",
            "conditions": {"ref_name": {"include": ["refs/heads/master"]}},
            "rules": [{"type": "pull_request"}],
        }
    ]
    issues = task_session.validate_master_ruleset(weak)
    assert "master Ruleset is missing deletion" in issues
    assert "master Ruleset is missing required_status_checks" in issues

    strong = [
        {
            "target": "branch",
            "enforcement": "active",
            "conditions": {"ref_name": {"include": ["refs/heads/master"]}},
            "rules": [
                {"type": "deletion"},
                {"type": "non_fast_forward"},
                {"type": "pull_request"},
                {
                    "type": "required_status_checks",
                    "parameters": {
                        "strict_required_status_checks_policy": True,
                        "required_status_checks": [{"context": "checks"}],
                    },
                },
            ],
        }
    ]
    assert task_session.validate_master_ruleset(strong) == []


def test_start_uses_exact_origin_master_and_records_no_dev_lane(
    repository: tuple[Path, Any],
) -> None:
    root, git_repository = repository
    _write_task(root, "201", "start-me")
    controller = task_session.TaskController(
        git_repository, github=FakeGitHub(git_repository.ref("origin/master"))
    )

    started = controller.start("201", owner_launch=True, session_label="pytest", offline=True)
    lease = started["lease"]
    assert lease["base_origin_master_sha"] == git_repository.ref("origin/master")
    assert lease["target_base_branch"] == "master"
    assert lease["integration_policy"] == "task-pr-to-master"
    assert "base_origin_dev_sha" not in lease
    assert "PR master" in started["prompt"]


def test_mark_ready_requires_current_pre_push_pass_and_rejects_stale_evidence(
    repository: tuple[Path, Any],
) -> None:
    root, git_repository, controller, worktree, branch, sha_pair = _prepare_started(
        repository, "202"
    )
    base_sha, head_sha = sha_pair.split(":")
    _write_gate_evidence(
        controller,
        "202",
        branch=branch,
        head_sha=head_sha,
        base_sha=base_sha,
        terminal_result="PLAN_ONLY",
    )
    with pytest.raises(task_session.TaskSessionError, match="PRE_PUSH_CI_PASS"):
        controller.mark_ready(
            "202", head_sha=head_sha, review_verdict="APPROVED", qa_verdict="PASS"
        )

    _write_gate_evidence(controller, "202", branch=branch, head_sha=head_sha, base_sha=base_sha)
    ready = controller.mark_ready(
        "202", head_sha=head_sha, review_verdict="APPROVED", qa_verdict="PASS"
    )
    assert ready["lifecycle_state"] == "ready-for-pr"
    assert ready["pre_push_ci_pass"]["head_sha"] == head_sha
    assert root == controller._canonical_root()
    assert git_repository.status(worktree) == []


def test_record_production_success_requires_exact_merged_master_deployment(
    repository: tuple[Path, Any],
) -> None:
    root, _, controller, _, branch, sha_pair = _prepare_started(repository, "203")
    base_sha, head_sha = sha_pair.split(":")
    _write_gate_evidence(controller, "203", branch=branch, head_sha=head_sha, base_sha=base_sha)
    controller.mark_ready("203", head_sha=head_sha, review_verdict="APPROVED", qa_verdict="PASS")

    _git(root, "merge", "--no-ff", branch, "-m", "Merge task 203")
    merge_sha = _git(root, "rev-parse", "HEAD")
    _git(root, "push", "origin", "master")
    github = controller.github
    assert isinstance(github, FakeGitHub)
    github.master_sha = merge_sha
    github.pulls[203] = _task_pr(203, "203", base_sha, head_sha, merge_sha=merge_sha)
    github.commits[203] = [_task_commit("203")]
    github.files[203] = [{"filename": "change.txt"}]
    github.checks[head_sha] = [_success_check(head_sha)]
    github.successful_deployments.add((merge_sha, "production"))
    github.associated_pulls = [github.pulls[203]]

    history = controller.record_production_success(
        "203", pr_number=203, merge_sha=merge_sha, deployed_sha=merge_sha
    )
    assert history["state"] == "production-success"
    assert history["deployed_sha"] == merge_sha
    assert controller.store.read_json(controller.store.task_lease_path("203"))[
        "lifecycle_state"
    ] == ("production-success")


def test_record_production_success_rejects_sha_mismatch_without_mutation(
    repository: tuple[Path, Any],
) -> None:
    _, _, controller, _, _, sha_pair = _prepare_started(repository, "204")
    base_sha, head_sha = sha_pair.split(":")
    lease = controller.store.read_json(controller.store.task_lease_path("204"))
    _write_gate_evidence(
        controller, "204", branch=lease["branch"], head_sha=head_sha, base_sha=base_sha
    )
    controller.mark_ready("204", head_sha=head_sha, review_verdict="APPROVED", qa_verdict="PASS")
    with pytest.raises(task_session.TaskSessionError, match="equal the exact merged master SHA"):
        controller.record_production_success(
            "204", pr_number=204, merge_sha="a" * 40, deployed_sha=head_sha
        )
    assert controller.store.read_json(controller.store.task_lease_path("204"))[
        "lifecycle_state"
    ] == ("ready-for-pr")


def test_verify_master_merge_accepts_only_one_task_pr_for_current_master() -> None:
    base_sha = "a" * 40
    merge_sha = "c" * 40
    github = FakeGitHub(merge_sha)
    github.associated_pulls = [_task_pr(205, "205", base_sha, "b" * 40, merge_sha=merge_sha)]
    result = task_session.verify_master_merge(object(), github, sha=merge_sha)
    assert result["kind"] == "task-pr-merge"
    assert result["pull_request"]["number"] == 205


def test_recover_is_read_only_and_preserves_dirty_unique_task_state(
    repository: tuple[Path, Any],
) -> None:
    _, _, controller, worktree, _, _ = _prepare_started(repository, "206")
    (worktree / "unique.txt").write_text("unique\n", encoding="utf-8")
    _git(worktree, "add", "unique.txt")
    _git(worktree, "commit", "-m", "feat: [Task 206] unique recovery state")
    (worktree / "dirty.txt").write_text("dirty\n", encoding="utf-8")

    result = controller.recover("206")

    assert result["classification"] == "RECOVERY_REQUIRED"
    assert result["mutation_performed"] is False
    assert any(item["dirty"] for item in result["worktrees"])
    assert any(item["unique_commits"] for item in result["worktrees"])
    assert (worktree / "dirty.txt").exists()


def test_finish_cleans_exact_production_success_state(repository: tuple[Path, Any]) -> None:
    root, git_repository, controller, worktree, branch, sha_pair = _prepare_started(
        repository, "207"
    )
    base_sha, head_sha = sha_pair.split(":")
    _write_gate_evidence(controller, "207", branch=branch, head_sha=head_sha, base_sha=base_sha)
    controller.mark_ready("207", head_sha=head_sha, review_verdict="APPROVED", qa_verdict="PASS")
    _git(root, "merge", "--no-ff", branch, "-m", "Merge task 207")
    merge_sha = _git(root, "rev-parse", "HEAD")
    _git(root, "push", "origin", "master")
    github = controller.github
    assert isinstance(github, FakeGitHub)
    github.pulls[207] = _task_pr(207, "207", base_sha, head_sha, merge_sha=merge_sha)
    github.commits[207] = [_task_commit("207")]
    github.files[207] = [{"filename": "change.txt"}]
    github.checks[head_sha] = [_success_check(head_sha)]
    github.successful_deployments.add((merge_sha, "production"))
    controller.record_production_success(
        "207", pr_number=207, merge_sha=merge_sha, deployed_sha=merge_sha
    )

    result = controller.finish("207")

    assert result["cleanup_performed"] is True
    assert result["deleted_local_branch"] == branch
    assert not worktree.exists()
    assert not git_repository.ref_exists(branch)
    assert not controller.store.task_lease_path("207").exists()
    assert (
        controller.store.read_json(controller.store.history / "task-207.json")["state"]
        == "finished"
    )


def test_finish_refuses_dirty_worktree_and_preserves_state(repository: tuple[Path, Any]) -> None:
    root, git_repository, controller, worktree, branch, sha_pair = _prepare_started(
        repository, "208"
    )
    base_sha, head_sha = sha_pair.split(":")
    _write_gate_evidence(controller, "208", branch=branch, head_sha=head_sha, base_sha=base_sha)
    controller.mark_ready("208", head_sha=head_sha, review_verdict="APPROVED", qa_verdict="PASS")
    _git(root, "merge", "--no-ff", branch, "-m", "Merge task 208")
    merge_sha = _git(root, "rev-parse", "HEAD")
    _git(root, "push", "origin", "master")
    github = controller.github
    assert isinstance(github, FakeGitHub)
    github.successful_deployments.add((merge_sha, "production"))
    github.pulls[208] = _task_pr(208, "208", base_sha, head_sha, merge_sha=merge_sha)
    github.commits[208] = [_task_commit("208")]
    github.files[208] = [{"filename": "change.txt"}]
    github.checks[head_sha] = [_success_check(head_sha)]
    controller.record_production_success(
        "208", pr_number=208, merge_sha=merge_sha, deployed_sha=merge_sha
    )
    (worktree / "uncommitted.txt").write_text("preserve\n", encoding="utf-8")

    with pytest.raises(task_session.TaskSessionError, match="refuses dirty task worktree"):
        controller.finish("208")

    assert worktree.exists()
    assert git_repository.ref_exists(branch)
    assert controller.store.task_lease_path("208").exists()
