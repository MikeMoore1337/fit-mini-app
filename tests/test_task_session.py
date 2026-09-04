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


def _write_task(
    root: Path,
    task_id: str,
    slug: str,
    *,
    dependencies: str = "",
    concurrency: str = "exclusive-write",
    owner_gate: str = "explicit-launch",
) -> Path:
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
        f"concurrency: {concurrency}\n"
        f"owner_gate: {owner_gate}\n"
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
    repository: tuple[Path, Any], task_id: str = "301", *, concurrency: str = "exclusive-write"
) -> tuple[Path, Any, Any, Path, str, str]:
    root, git_repository = repository
    _write_task(root, task_id, "synthetic-task", concurrency=concurrency)
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
    from scripts.ci_contract import CONTRACT_VERSION, contract_digest
    from scripts.pre_push_gate import _evidence_digest

    path = controller._gate_evidence_path(controller._canonical_root(), task_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "evidence_version": 1,
        "contract_version": CONTRACT_VERSION,
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
    lease = controller.store.read_json(controller.store.task_lease_path(task_id))
    if isinstance(lease, dict) and lease.get("delivery_generation") is not None:
        payload["delivery_generation"] = lease["delivery_generation"]
    payload["evidence_digest"] = _evidence_digest(payload)
    path.write_text(
        json.dumps(payload),
        encoding="utf-8",
    )
    return path


def _commit_task(worktree: Path, task_id: str, filename: str = "change.txt") -> str:
    (worktree / filename).write_text(f"{task_id}\n", encoding="utf-8")
    _git(worktree, "add", filename)
    _git(worktree, "commit", "-m", f"feat: [Task {task_id}] synthetic change")
    return _git(worktree, "rev-parse", "HEAD")


def _prepare_delivery(controller: Any, task_id: str, *, branch: str) -> dict[str, Any]:
    acquired = controller.acquire_delivery(task_id)
    assert acquired["acquired"] is True
    refreshed = controller.refresh_for_delivery(task_id)
    refreshed_head = _git(Path(refreshed["worktree"]), "rev-parse", "HEAD")
    _write_gate_evidence(
        controller,
        task_id,
        branch=branch,
        head_sha=refreshed_head,
        base_sha=refreshed["base_origin_master_sha"],
    )
    return controller.validate_delivery(task_id)


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


def test_task_commit_messages_allow_only_declared_hard_dependencies() -> None:
    messages = [
        "feat: [Task 133] provide dependency",
        "feat: [Task 135] consume dependency\n\nDepends-on: [Task 133], [Task 134]",
    ]

    task_session.validate_task_commit_messages("135", messages, dependency_ids=("133", "134"))

    with pytest.raises(task_session.TaskSessionError, match="declared hard dependency"):
        task_session.validate_task_commit_messages(
            "135",
            [*messages, "fix: [Task 136] unrelated change"],
            dependency_ids=("133", "134"),
        )


def test_task_pr_accepts_dependency_provenance_declared_in_task_commit() -> None:
    base_sha = "a" * 40
    head_sha = "b" * 40
    pull_request = _task_pr(135, "135", base_sha, head_sha)
    pull_request["commits"] = 2
    commits = [
        _task_commit("133"),
        {"commit": {"message": "feat: [Task 135] consume dependency\n\nDepends-on: [Task 133]"}},
    ]

    assert (
        task_session.validate_task_pull_request(
            pull_request,
            commits,
            [_success_check(head_sha)],
            expected_base_sha=base_sha,
            dependency_ids=None,
        )
        == "135"
    )


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


def test_two_independent_write_tasks_get_distinct_leases_and_worktrees(
    repository: tuple[Path, Any],
) -> None:
    root, git_repository = repository
    for task_id in ("220", "221"):
        _write_task(root, task_id, f"parallel-{task_id}", concurrency="independent-write")
    controller = task_session.TaskController(
        git_repository, github=FakeGitHub(git_repository.ref("origin/master"))
    )

    first = controller.start("220", owner_launch=True, session_label="parallel-a", offline=True)
    second = controller.start("221", owner_launch=True, session_label="parallel-b", offline=True)

    assert first["lease"]["concurrency_class"] == "independent-write"
    assert second["lease"]["concurrency_class"] == "independent-write"
    assert first["lease"]["worktree"] != second["lease"]["worktree"]
    assert {item["task_id"] for item in controller.store.all_leases()} == {"220", "221"}


def test_three_independent_write_tasks_can_run_at_once(
    repository: tuple[Path, Any],
) -> None:
    root, git_repository = repository
    for task_id in ("222", "223", "224"):
        _write_task(root, task_id, f"parallel-{task_id}", concurrency="independent-write")
    controller = task_session.TaskController(git_repository)

    started = [
        controller.start(
            task_id, owner_launch=True, session_label=f"parallel-{task_id}", offline=True
        )
        for task_id in ("222", "223", "224")
    ]

    assert len({item["lease"]["worktree"] for item in started}) == 3
    assert all(item["lease"]["lifecycle_state"] == "implementation" for item in started)


@pytest.mark.parametrize(
    ("existing_class", "candidate_class"),
    [
        ("exclusive-write", "independent-write"),
        ("independent-write", "exclusive-write"),
        ("exclusive-write", "exclusive-write"),
    ],
)
def test_exclusive_write_is_a_real_implementation_blocker(
    repository: tuple[Path, Any], existing_class: str, candidate_class: str
) -> None:
    root, git_repository = repository
    _write_task(root, "225", "existing", concurrency=existing_class)
    _write_task(root, "226", "candidate", concurrency=candidate_class)
    controller = task_session.TaskController(git_repository)
    controller.start("225", owner_launch=True, session_label="existing", offline=True)

    with pytest.raises(
        task_session.TaskSessionError, match="incompatible implementation write lease"
    ):
        controller.start("226", owner_launch=True, session_label="candidate", offline=True)


def test_adopt_current_uses_same_compatible_lease_contract(
    repository: tuple[Path, Any],
) -> None:
    root, git_repository = repository
    _write_task(root, "227", "existing", concurrency="independent-write")
    _write_task(root, "228", "adopted", concurrency="independent-write")
    controller = task_session.TaskController(git_repository)
    controller.start("227", owner_launch=True, session_label="existing", offline=True)
    adopted_path = root / ".artifacts" / "worktrees" / "adopted-228"
    _git(root, "worktree", "add", "-b", "task/228-adopted", str(adopted_path), "origin/master")

    adopted_controller = task_session.TaskController(task_session.GitRepository(adopted_path))
    lease = adopted_controller.adopt_current("228", owner_launch=True, session_label="adopted")

    assert lease["task_id"] == "228"
    assert lease["concurrency_class"] == "independent-write"


def test_active_production_deploy_blocks_only_delivery_acquisition(
    repository: tuple[Path, Any],
) -> None:
    root, git_repository = repository
    for task_id in ("230", "231"):
        _write_task(root, task_id, f"deploy-{task_id}", concurrency="independent-write")
    github = FakeGitHub(git_repository.ref("origin/master"))
    github.active_runs = [{"name": "Deploy production", "status": "in_progress"}]
    controller = task_session.TaskController(git_repository, github=github)

    first = controller.start("230", owner_launch=True, session_label="deploy-a")
    second = controller.start("231", owner_launch=True, session_label="deploy-b")
    second_lease = second["lease"]
    second_head = _commit_task(Path(second_lease["worktree"]), "231")
    controller.mark_ready("231", head_sha=second_head, review_verdict="APPROVED", qa_verdict="PASS")

    waiting = controller.acquire_delivery("231")

    assert first["lease"]["worktree"] != second_lease["worktree"]
    assert waiting["acquired"] is False
    assert waiting["delivery_blocker"] == "active production deployment"
    assert controller.store.read_json(controller.store.task_lease_path("231"))[
        "lifecycle_state"
    ] == ("waiting-for-delivery")

    github.active_runs = []
    acquired = controller.acquire_delivery("231")
    assert acquired["acquired"] is True
    assert acquired["lifecycle_state"] == "delivering"


def test_delivery_lane_is_serial_and_handoff_is_deterministic(
    repository: tuple[Path, Any],
) -> None:
    root, git_repository = repository
    for task_id in ("232", "233"):
        _write_task(root, task_id, f"queue-{task_id}", concurrency="independent-write")
    controller = task_session.TaskController(git_repository)
    started = {
        task_id: controller.start(
            task_id, owner_launch=True, session_label=f"queue-{task_id}", offline=True
        )
        for task_id in ("232", "233")
    }
    for task_id in ("232", "233"):
        head_sha = _commit_task(Path(started[task_id]["lease"]["worktree"]), task_id)
        controller.mark_ready(
            task_id, head_sha=head_sha, review_verdict="APPROVED", qa_verdict="PASS"
        )

    first = controller.acquire_delivery("232", offline=True)
    second = controller.acquire_delivery("233", offline=True)
    assert first["acquired"] is True
    assert second["acquired"] is False
    assert second["delivery_owner"] == "232"
    assert controller.store.read_json(controller.store.task_lease_path("233"))[
        "lifecycle_state"
    ] == ("waiting-for-delivery")

    released = controller.release_delivery("232", reason="synthetic delivery interruption")

    assert released["lifecycle_state"] == "recovery-required"
    assert controller.store.delivery_state()["owner"]["task_id"] == "233"
    assert controller.store.read_json(controller.store.task_lease_path("233"))[
        "lifecycle_state"
    ] == ("delivering")


def test_busy_delivery_lane_does_not_block_compatible_implementation(
    repository: tuple[Path, Any],
) -> None:
    root, git_repository = repository
    for task_id in ("240", "241", "242"):
        _write_task(root, task_id, f"busy-{task_id}", concurrency="independent-write")
    controller = task_session.TaskController(git_repository)
    first = controller.start("240", owner_launch=True, session_label="busy-a", offline=True)
    first_worktree = Path(first["lease"]["worktree"])
    first_head = _commit_task(first_worktree, "240")
    controller.mark_ready("240", head_sha=first_head, review_verdict="APPROVED", qa_verdict="PASS")
    acquired = controller.acquire_delivery("240", offline=True)

    second = controller.start("241", owner_launch=True, session_label="busy-b", offline=True)
    third = controller.start("242", owner_launch=True, session_label="busy-c", offline=True)

    assert acquired["acquired"] is True
    assert second["lease"]["lifecycle_state"] == "implementation"
    assert third["lease"]["lifecycle_state"] == "implementation"


def test_refresh_updates_stale_task_base_and_invalidates_old_exact_head_evidence(
    repository: tuple[Path, Any],
) -> None:
    root, git_repository, controller, _, branch, sha_pair = _prepare_started(
        repository, "234", concurrency="independent-write"
    )
    old_base, old_head = sha_pair.split(":")
    _write_gate_evidence(controller, "234", branch=branch, head_sha=old_head, base_sha=old_base)
    controller.mark_ready("234", head_sha=old_head, review_verdict="APPROVED", qa_verdict="PASS")

    (root / "master-refresh.txt").write_text("M1\n", encoding="utf-8")
    _git(root, "add", "master-refresh.txt")
    _git(root, "commit", "-m", "chore: advance master for delivery refresh")
    _git(root, "push", "origin", "master")
    github = controller.github
    assert isinstance(github, FakeGitHub)
    github.master_sha = git_repository.ref("origin/master")

    controller.acquire_delivery("234", offline=True)
    refreshed = controller.refresh_for_delivery("234")
    new_head = refreshed["delivery_head_sha"]

    assert refreshed["base_origin_master_sha"] != old_base
    assert new_head != old_head
    assert refreshed["pre_push_ci_pass"] is None
    assert refreshed["local_evidence"]["status"] == "invalidated-after-master-refresh"
    with pytest.raises(task_session.TaskSessionError, match="does not match current lease/HEAD"):
        controller.validate_delivery("234")

    _write_gate_evidence(
        controller,
        "234",
        branch=branch,
        head_sha=new_head,
        base_sha=refreshed["base_origin_master_sha"],
    )
    validated = controller.validate_delivery("234")
    assert validated["lifecycle_state"] == "delivery-gate"
    assert validated["delivery_gate_pass"]["head_sha"] == new_head


def test_refresh_requires_new_evidence_when_head_and_base_are_unchanged(
    repository: tuple[Path, Any],
) -> None:
    _, _, controller, _, branch, sha_pair = _prepare_started(
        repository, "243", concurrency="independent-write"
    )
    base_sha, head_sha = sha_pair.split(":")
    _write_gate_evidence(controller, "243", branch=branch, head_sha=head_sha, base_sha=base_sha)
    controller.mark_ready("243", head_sha=head_sha, review_verdict="APPROVED", qa_verdict="PASS")

    controller.acquire_delivery("243", offline=True)
    refreshed = controller.refresh_for_delivery("243", offline=True)

    assert refreshed["delivery_head_sha"] == head_sha
    with pytest.raises(
        task_session.TaskSessionError,
        match="earlier delivery refresh generation",
    ):
        controller.validate_delivery("243", offline=True)

    _write_gate_evidence(
        controller,
        "243",
        branch=branch,
        head_sha=head_sha,
        base_sha=refreshed["base_origin_master_sha"],
    )
    validated = controller.validate_delivery("243", offline=True)
    assert validated["pre_push_ci_pass"]["delivery_generation"] == refreshed["delivery_generation"]


def test_local_master_behind_remote_is_informational_and_start_uses_remote_base(
    repository: tuple[Path, Any],
) -> None:
    root, git_repository = repository
    remote_worktree = root.parent / "remote-master"
    _git(root, "worktree", "add", "--detach", str(remote_worktree), "HEAD")
    try:
        (remote_worktree / "remote-change.txt").write_text("remote\n", encoding="utf-8")
        _git(remote_worktree, "add", "remote-change.txt")
        _git(remote_worktree, "commit", "-m", "chore: advance remote master")
        _git(remote_worktree, "push", "origin", "HEAD:master")
    finally:
        _git(root, "worktree", "remove", "--force", str(remote_worktree))
    _git(root, "fetch", "origin", "master")
    _write_task(root, "235", "behind-remote", concurrency="independent-write")
    controller = task_session.TaskController(git_repository)

    report = controller.doctor(offline=True)
    started = controller.start("235", owner_launch=True, session_label="behind", offline=True)

    assert git_repository.ahead_behind("master", "origin/master") == (0, 1)
    assert any("behind" in item for item in report["informational_findings"])
    assert report["implementation_blockers"] == []
    assert started["lease"]["base_origin_master_sha"] == git_repository.ref("origin/master")


def test_local_master_unique_commit_is_a_fail_closed_start_blocker(
    repository: tuple[Path, Any],
) -> None:
    root, git_repository = repository
    (root / "unpublished.txt").write_text("local\n", encoding="utf-8")
    _git(root, "add", "unpublished.txt")
    _git(root, "commit", "-m", "chore: unpublished local master change")
    _write_task(root, "236", "diverged", concurrency="independent-write")
    controller = task_session.TaskController(git_repository)

    report = controller.doctor(offline=True)

    assert any("unpublished commits" in item for item in report["implementation_blockers"])
    with pytest.raises(task_session.TaskSessionError, match="implementation/start blockers"):
        controller.start("236", owner_launch=True, session_label="diverged", offline=True)


def test_doctor_does_not_turn_compatible_leases_into_global_error(
    repository: tuple[Path, Any],
) -> None:
    root, git_repository = repository
    for task_id in ("237", "238"):
        _write_task(root, task_id, f"doctor-{task_id}", concurrency="independent-write")
    controller = task_session.TaskController(git_repository)
    controller.start("237", owner_launch=True, session_label="doctor-a", offline=True)
    controller.start("238", owner_launch=True, session_label="doctor-b", offline=True)

    report = controller.doctor(offline=True)

    assert report["safe_for_implementation"] is True
    assert not any("active task write lease" in item for item in report["issues"])
    assert [item["task_id"] for item in report["leases"]] == ["237", "238"]


def test_owner_selected_launch_requires_only_explicit_launch_unless_concrete_gate_declared(
    repository: tuple[Path, Any],
) -> None:
    root, git_repository = repository
    _write_task(root, "239", "concrete-gate", owner_gate="HUMAN_EVIDENCE: Telegram screenshot")
    controller = task_session.TaskController(git_repository)

    with pytest.raises(
        task_session.TaskSessionError,
        match="Task 239 blocked: HUMAN_EVIDENCE is missing: Telegram screenshot",
    ):
        controller.start("239", owner_launch=True, session_label="gate", offline=True)


def test_mark_ready_persists_ready_state_without_old_base_pre_push_pass(
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
    ready = controller.mark_ready(
        "202", head_sha=head_sha, review_verdict="APPROVED", qa_verdict="PASS"
    )
    assert ready["lifecycle_state"] == "ready-for-delivery"
    assert ready["local_evidence"]["status"] == "pending-final-delivery-gate"

    _write_gate_evidence(controller, "202", branch=branch, head_sha=head_sha, base_sha=base_sha)
    ready = controller.mark_ready(
        "202", head_sha=head_sha, review_verdict="APPROVED", qa_verdict="PASS"
    )
    assert ready["lifecycle_state"] == "ready-for-delivery"
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

    _prepare_delivery(controller, "203", branch=branch)

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
    _prepare_delivery(controller, "204", branch=lease["branch"])
    with pytest.raises(task_session.TaskSessionError, match="equal the exact merged master SHA"):
        controller.record_production_success(
            "204", pr_number=204, merge_sha="a" * 40, deployed_sha=head_sha
        )
    assert controller.store.read_json(controller.store.task_lease_path("204"))[
        "lifecycle_state"
    ] == ("delivery-gate")


def test_record_production_success_rejects_gate_invalidated_during_finalization(
    repository: tuple[Path, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _, controller, _, branch, sha_pair = _prepare_started(repository, "204A")
    base_sha, head_sha = sha_pair.split(":")
    _write_gate_evidence(controller, "204A", branch=branch, head_sha=head_sha, base_sha=base_sha)
    controller.mark_ready("204A", head_sha=head_sha, review_verdict="APPROVED", qa_verdict="PASS")
    _prepare_delivery(controller, "204A", branch=branch)

    _git(root, "merge", "--no-ff", branch, "-m", "Merge task 204A")
    merge_sha = _git(root, "rev-parse", "HEAD")
    _git(root, "push", "origin", "master")
    github = controller.github
    assert isinstance(github, FakeGitHub)
    github.master_sha = merge_sha
    github.pulls[214] = _task_pr(214, "204A", base_sha, head_sha, merge_sha=merge_sha)
    github.commits[214] = [_task_commit("204A")]
    github.files[214] = [{"filename": "change.txt"}]
    github.checks[head_sha] = [_success_check(head_sha)]
    github.successful_deployments.add((merge_sha, "production"))

    original_gate = controller._current_gate_evidence
    calls = 0

    def invalidate_after_first_check(*args: Any, **kwargs: Any) -> dict[str, Any]:
        nonlocal calls
        result = original_gate(*args, **kwargs)
        calls += 1
        if calls == 1:
            lease_path = controller.store.task_lease_path("204A")
            lease = controller.store.read_json(lease_path)
            assert isinstance(lease, dict)
            lease["lifecycle_state"] = "delivering"
            task_session.StateStore.replace_json(lease_path, lease)
        return result

    monkeypatch.setattr(controller, "_current_gate_evidence", invalidate_after_first_check)

    with pytest.raises(
        task_session.TaskSessionError,
        match="no longer in the validated final delivery-gate state",
    ):
        controller.record_production_success(
            "204A", pr_number=214, merge_sha=merge_sha, deployed_sha=merge_sha
        )

    assert calls == 1
    assert not (controller.store.history / "task-204A.json").exists()


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

    assert result["classification"] == "STALE_OR_INTERRUPTED"
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
    _prepare_delivery(controller, "207", branch=branch)
    _git(root, "merge", "--no-ff", branch, "-m", "Merge task 207")
    merge_sha = _git(root, "rev-parse", "HEAD")
    _git(root, "push", "origin", "master")
    github = controller.github
    assert isinstance(github, FakeGitHub)
    github.master_sha = merge_sha
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


def test_finish_cleans_only_delivered_task_and_preserves_next_delivery_task(
    repository: tuple[Path, Any],
) -> None:
    root, _, controller, _, branch, sha_pair = _prepare_started(
        repository, "209", concurrency="independent-write"
    )
    base_sha, head_sha = sha_pair.split(":")
    _write_gate_evidence(controller, "209", branch=branch, head_sha=head_sha, base_sha=base_sha)
    controller.mark_ready("209", head_sha=head_sha, review_verdict="APPROVED", qa_verdict="PASS")

    _write_task(root, "210", "queue-b", concurrency="independent-write")
    second = controller.start("210", owner_launch=True, session_label="queue-b", offline=True)
    second_worktree = Path(second["lease"]["worktree"])
    second_branch = str(second["lease"]["branch"])
    second_head = _commit_task(second_worktree, "210")
    controller.mark_ready("210", head_sha=second_head, review_verdict="APPROVED", qa_verdict="PASS")

    _prepare_delivery(controller, "209", branch=branch)
    _git(root, "merge", "--no-ff", branch, "-m", "Merge task 209")
    merge_sha = _git(root, "rev-parse", "HEAD")
    _git(root, "push", "origin", "master")
    github = controller.github
    assert isinstance(github, FakeGitHub)
    github.master_sha = merge_sha
    github.pulls[209] = _task_pr(209, "209", base_sha, head_sha, merge_sha=merge_sha)
    github.commits[209] = [_task_commit("209")]
    github.files[209] = [{"filename": "change.txt"}]
    github.checks[head_sha] = [_success_check(head_sha)]
    github.successful_deployments.add((merge_sha, "production"))
    controller.record_production_success(
        "209", pr_number=209, merge_sha=merge_sha, deployed_sha=merge_sha
    )
    assert controller.store.delivery_state()["owner"]["task_id"] == "209"

    controller.finish("209")

    assert not (root / ".artifacts" / "worktrees" / branch.removeprefix("task/")).exists()
    assert second_worktree.exists()
    assert controller.store.task_lease_path("210").exists()
    assert controller.store.delivery_state()["owner"]["task_id"] == "210"
    assert controller.store.read_json(controller.store.task_lease_path("210"))["branch"] == (
        second_branch
    )


def test_finish_refuses_dirty_worktree_and_preserves_state(repository: tuple[Path, Any]) -> None:
    root, git_repository, controller, worktree, branch, sha_pair = _prepare_started(
        repository, "208"
    )
    base_sha, head_sha = sha_pair.split(":")
    _write_gate_evidence(controller, "208", branch=branch, head_sha=head_sha, base_sha=base_sha)
    controller.mark_ready("208", head_sha=head_sha, review_verdict="APPROVED", qa_verdict="PASS")
    _prepare_delivery(controller, "208", branch=branch)
    _git(root, "merge", "--no-ff", branch, "-m", "Merge task 208")
    merge_sha = _git(root, "rev-parse", "HEAD")
    _git(root, "push", "origin", "master")
    github = controller.github
    assert isinstance(github, FakeGitHub)
    github.master_sha = merge_sha
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
