from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from contextlib import contextmanager
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


def test_run_decodes_command_output_as_utf8(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    observed: dict[str, Any] = {}

    def fake_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        observed.update(kwargs)
        return subprocess.CompletedProcess(args[0], 0, stdout="ветка\n", stderr="")

    monkeypatch.setattr(task_session.subprocess, "run", fake_run)

    completed = task_session._run(["gh", "api", "repos/owner/repository"], cwd=tmp_path)

    assert completed.stdout == "ветка\n"
    assert observed["text"] is True
    assert observed["encoding"] == "utf-8"


def _git(path: Path, *args: str) -> str:
    completed = subprocess.run(["git", *args], cwd=path, check=True, text=True, capture_output=True)
    return completed.stdout.strip()


def _write_task(root: Path, task_id: str, slug: str, *, body: str = "") -> Path:
    tasks = root / "codex-backlog" / "tasks"
    tasks.mkdir(parents=True, exist_ok=True)
    path = tasks / f"{task_id}-{slug}.md"
    path.write_text(
        f"# Task {task_id}\n\n"
        "- **Статус:** owner-selected, not started\n"
        "- **Тип:** implementation\n"
        f"{body}\n",
        encoding="utf-8",
    )
    return path


@pytest.fixture
def repository(tmp_path: Path) -> tuple[Path, Any]:
    root = tmp_path / "repository with spaces"
    remote = tmp_path / "remote.git"
    root.mkdir()
    _git(root, "init", "-b", "dev")
    _git(root, "config", "user.name", "Task Session Tests")
    _git(root, "config", "user.email", "task-session@example.invalid")
    (root / ".github").mkdir()
    (root / ".github" / "deployed-sync-app.json").write_text(
        '{"app_id": 123, "app_slug": "test-sync"}\n', encoding="utf-8"
    )
    (root / ".gitignore").write_text("/codex-backlog/tasks/\n.artifacts/\n", encoding="utf-8")
    (root / "README.md").write_text("initial\n", encoding="utf-8")
    _git(root, "add", ".github/deployed-sync-app.json", ".gitignore", "README.md")
    _git(root, "commit", "-m", "chore: initial")
    _git(tmp_path, "init", "--bare", str(remote))
    _git(root, "remote", "add", "origin", str(remote))
    _git(root, "push", "-u", "origin", "dev")
    _git(root, "branch", "master")
    _git(root, "push", "origin", "master")
    _git(root, "fetch", "origin")
    return root, task_session.GitRepository(root)


class FakeGitHub:
    def __init__(self, dev_sha: str) -> None:
        self.dev_sha = dev_sha
        self.master_sha = dev_sha
        self.pulls: dict[int, dict[str, Any]] = {}
        self.commits: dict[int, list[dict[str, Any]]] = {}
        self.files: dict[int, list[dict[str, Any]]] = {}
        self.checks: dict[str, list[dict[str, Any]]] = {}
        self.runs: dict[str, list[dict[str, Any]]] = {}
        self.open_prs: list[dict[str, Any]] = []
        self.active_runs: list[dict[str, Any]] = []
        self.ruleset_payload: list[dict[str, Any]] = []

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
        return self.dev_sha if branch == "dev" else self.master_sha

    def workflow_runs(self, workflow: str, sha: str) -> list[dict[str, Any]]:
        return self.runs.get(sha, [])

    def active_workflow_runs(self) -> list[dict[str, Any]]:
        return self.active_runs

    def rulesets(self) -> list[dict[str, Any]]:
        return self.ruleset_payload


def _task_pr(number: int, task_id: str, base_sha: str, head_sha: str) -> dict[str, Any]:
    return {
        "number": number,
        "title": f"[Task {task_id}] Synthetic task",
        "merged_at": None,
        "merge_commit_sha": None,
        "base": {
            "ref": "dev",
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


def _task_lease(
    controller: Any,
    task_id: str,
    root: Path,
    base_sha: str,
    *,
    ready_head_sha: str | None = None,
    mode: str = "write",
) -> None:
    controller.store.initialize()
    controller.store.create_json(
        controller.store.task_lease_path(task_id),
        {
            "version": 1,
            "task_id": task_id,
            "canonical_task_path": str(root / "codex-backlog" / "tasks" / f"{task_id}-x.md"),
            "branch": f"task/{task_id}-synthetic-task",
            "worktree": str(root / ".artifacts" / "worktrees" / task_id),
            "base_origin_dev_sha": base_sha,
            "mode": mode,
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
            "lifecycle_state": "ready-integration" if ready_head_sha else "implementation",
            "session_label": "test",
            "ready_head_sha": ready_head_sha,
        },
    )


@pytest.mark.parametrize("task_id", ["127", "90A", "124C"])
def test_task_ids_and_branch_traceability_accept_numeric_and_suffix_ids(task_id: str) -> None:
    branch = f"task/{task_id}-valid-kebab"
    assert task_session.task_id_from_branch(branch) == task_id
    task_session.validate_task_commit_messages(task_id, [f"fix: [Task {task_id}] preserve trace"])


@pytest.mark.parametrize(
    "branch",
    ["feature/127-x", "task/127", "task/127-Bad-Slug", "task/127_bad", "task/A127-test"],
)
def test_invalid_task_branch_names_fail_closed(branch: str) -> None:
    with pytest.raises(task_session.TaskSessionError, match="must match"):
        task_session.task_id_from_branch(branch)


def test_missing_mismatched_and_mixed_task_commit_ids_fail_closed() -> None:
    with pytest.raises(task_session.TaskSessionError, match="exactly"):
        task_session.validate_task_commit_messages("127", ["fix: missing task ID"])
    with pytest.raises(task_session.TaskSessionError, match="exactly"):
        task_session.validate_task_commit_messages("127", ["fix: [Task 126] wrong task"])
    with pytest.raises(task_session.TaskSessionError, match="exactly"):
        task_session.validate_task_commit_messages(
            "127", ["fix: [Task 127] accidentally mixes [Task 128]"]
        )


def test_start_creates_branch_worktree_from_exact_origin_dev_and_canonical_task_path(
    repository: tuple[Path, Any],
) -> None:
    root, git_repository = repository
    task_path = _write_task(root, "201", "windows-path-test")
    controller = task_session.TaskController(
        git_repository, github=FakeGitHub(git_repository.ref("origin/dev"))
    )

    result = controller.start("201", owner_launch=True, session_label="pytest", offline=True)

    lease = result["lease"]
    worktree = Path(lease["worktree"])
    assert lease["base_origin_dev_sha"] == git_repository.ref("origin/dev")
    assert lease["branch"] == "task/201-windows-path-test"
    assert Path(lease["canonical_task_path"]) == task_path.resolve()
    assert worktree.is_dir()
    assert not (worktree / "codex-backlog" / "tasks" / task_path.name).exists()
    assert str(worktree).startswith(str(root / ".artifacts" / "worktrees"))


def test_start_refuses_dirty_main_dev(repository: tuple[Path, Any]) -> None:
    root, git_repository = repository
    _write_task(root, "202", "dirty-main")
    (root / "README.md").write_text("dirty\n", encoding="utf-8")
    controller = task_session.TaskController(
        git_repository, github=FakeGitHub(git_repository.ref("origin/dev"))
    )

    with pytest.raises(task_session.TaskSessionError, match="main dev worktree is dirty"):
        controller.start("202", owner_launch=True, session_label="pytest", offline=True)


def test_mark_ready_requires_clean_exact_head_and_records_review_qa(
    repository: tuple[Path, Any],
) -> None:
    root, git_repository = repository
    _write_task(root, "211", "ready-evidence")
    controller = task_session.TaskController(
        git_repository, github=FakeGitHub(git_repository.ref("origin/dev"))
    )
    started = controller.start("211", owner_launch=True, session_label="pytest", offline=True)
    worktree = Path(started["lease"]["worktree"])
    (worktree / "change.txt").write_text("ready\n", encoding="utf-8")
    _git(worktree, "add", "change.txt")
    _git(worktree, "commit", "-m", "feat: [Task 211] add ready evidence")
    head_sha = _git(worktree, "rev-parse", "HEAD")

    ready = controller.mark_ready(
        "211", head_sha=head_sha, review_verdict="APPROVED", qa_verdict="PASS"
    )

    assert ready["lifecycle_state"] == "ready-integration"
    assert ready["ready_head_sha"] == head_sha
    assert ready["review_verdict"] == "APPROVED"
    assert ready["qa_verdict"] == "PASS"


def test_mark_ready_replaces_evidence_before_queue_but_not_after_queue(
    repository: tuple[Path, Any],
) -> None:
    root, git_repository = repository
    _write_task(root, "212", "replacement-evidence")
    controller = task_session.TaskController(
        git_repository, github=FakeGitHub(git_repository.ref("origin/dev"))
    )
    started = controller.start("212", owner_launch=True, session_label="pytest", offline=True)
    worktree = Path(started["lease"]["worktree"])
    change = worktree / "change.txt"
    change.write_text("first\n", encoding="utf-8")
    _git(worktree, "add", "change.txt")
    _git(worktree, "commit", "-m", "feat: [Task 212] add first evidence")
    first_head = _git(worktree, "rev-parse", "HEAD")
    controller.mark_ready("212", head_sha=first_head, review_verdict="APPROVED", qa_verdict="PASS")

    change.write_text("second\n", encoding="utf-8")
    _git(worktree, "add", "change.txt")
    _git(worktree, "commit", "-m", "fix: [Task 212] update reviewed evidence")
    second_head = _git(worktree, "rev-parse", "HEAD")

    replaced = controller.mark_ready(
        "212", head_sha=second_head, review_verdict="APPROVED", qa_verdict="PASS"
    )
    assert replaced["ready_head_sha"] == second_head

    task_session.StateStore.replace_json(
        controller.store.queue_path,
        {"version": 1, "candidates": [{"task_id": "212"}]},
    )
    change.write_text("third\n", encoding="utf-8")
    _git(worktree, "add", "change.txt")
    _git(worktree, "commit", "-m", "fix: [Task 212] add queued evidence")
    third_head = _git(worktree, "rev-parse", "HEAD")

    with pytest.raises(task_session.TaskSessionError, match="readiness is immutable"):
        controller.mark_ready(
            "212", head_sha=third_head, review_verdict="APPROVED", qa_verdict="PASS"
        )


def test_start_refuses_local_dev_ahead_or_behind(repository: tuple[Path, Any]) -> None:
    root, git_repository = repository
    _write_task(root, "203", "ahead-dev")
    (root / "README.md").write_text("ahead\n", encoding="utf-8")
    _git(root, "add", "README.md")
    _git(root, "commit", "-m", "chore: local ahead")
    controller = task_session.TaskController(
        git_repository, github=FakeGitHub(git_repository.ref("origin/dev"))
    )

    with pytest.raises(task_session.TaskSessionError, match="local dev differs"):
        controller.start("203", owner_launch=True, session_label="pytest", offline=True)


def test_duplicate_start_and_incompatible_write_lane_fail_closed(
    repository: tuple[Path, Any],
) -> None:
    root, git_repository = repository
    _write_task(root, "204", "first-writer")
    _write_task(root, "205", "second-writer")
    controller = task_session.TaskController(
        git_repository, github=FakeGitHub(git_repository.ref("origin/dev"))
    )
    controller.start("204", owner_launch=True, session_label="pytest", offline=True)

    with pytest.raises(task_session.TaskSessionError, match=r"active lease|already"):
        controller.start("204", owner_launch=True, session_label="pytest", offline=True)
    with pytest.raises(task_session.TaskSessionError, match="incompatible"):
        controller.start("205", owner_launch=True, session_label="pytest", offline=True)


def test_owner_approved_compatible_write_cohort_can_prepare_in_parallel(
    repository: tuple[Path, Any],
) -> None:
    root, git_repository = repository
    metadata = "<!-- task-session\nconcurrency: independent-write\n-->"
    _write_task(root, "213", "parallel-one", body=metadata)
    _write_task(root, "214", "parallel-two", body=metadata)
    controller = task_session.TaskController(
        git_repository, github=FakeGitHub(git_repository.ref("origin/dev"))
    )

    first = controller.start("213", owner_launch=True, session_label="first", offline=True)
    second = controller.start("214", owner_launch=True, session_label="second", offline=True)

    assert first["lease"]["concurrency_class"] == "independent-write"
    assert second["lease"]["concurrency_class"] == "independent-write"


def test_unknown_or_different_write_cohorts_fail_closed(repository: tuple[Path, Any]) -> None:
    root, git_repository = repository
    _write_task(
        root,
        "215",
        "parallel-a",
        body="<!-- task-session\nconcurrency: independent-write\n-->",
    )
    _write_task(
        root,
        "216",
        "parallel-b",
        body="<!-- task-session\nconcurrency: exclusive-write\n-->",
    )
    _write_task(
        root,
        "217",
        "invalid-class",
        body="<!-- task-session\nconcurrency: parallel\n-->",
    )
    controller = task_session.TaskController(
        git_repository, github=FakeGitHub(git_repository.ref("origin/dev"))
    )
    controller.start("215", owner_launch=True, session_label="first", offline=True)

    with pytest.raises(task_session.TaskSessionError, match="incompatible"):
        controller.start("216", owner_launch=True, session_label="second", offline=True)
    with pytest.raises(task_session.TaskSessionError, match="Concurrency must be"):
        task_session.find_task_document(root, "217")


def test_research_readonly_sessions_can_coexist(repository: tuple[Path, Any]) -> None:
    root, git_repository = repository
    _write_task(root, "206", "research-one")
    _write_task(root, "207", "research-two")
    controller = task_session.TaskController(
        git_repository, github=FakeGitHub(git_repository.ref("origin/dev"))
    )

    first = controller.start(
        "206", owner_launch=True, session_label="research-1", mode="research-readonly", offline=True
    )
    second = controller.start(
        "207", owner_launch=True, session_label="research-2", mode="research-readonly", offline=True
    )

    assert first["lease"]["mode"] == second["lease"]["mode"] == "research-readonly"


def test_start_rejects_missing_dependency_umbrella_and_missing_owner_launch(
    repository: tuple[Path, Any],
) -> None:
    root, git_repository = repository
    _write_task(
        root,
        "208",
        "blocked-by-dependency",
        body="<!-- task-session\ndependencies: 999\n-->",
    )
    _write_task(root, "126", "umbrella", body="- **Тип:** umbrella\n")
    controller = task_session.TaskController(
        git_repository, github=FakeGitHub(git_repository.ref("origin/dev"))
    )

    with pytest.raises(task_session.TaskSessionError, match="owner-launch"):
        controller.start("208", owner_launch=False, session_label="pytest", offline=True)
    with pytest.raises(task_session.TaskSessionError, match="incomplete dependencies"):
        controller.start("208", owner_launch=True, session_label="pytest", offline=True)
    with pytest.raises(task_session.TaskSessionError, match="umbrella"):
        controller.start("126", owner_launch=True, session_label="pytest", offline=True)


def test_pending_task_metadata_is_machine_checkable(repository: tuple[Path, Any]) -> None:
    root, git_repository = repository
    _write_task(
        root,
        "209",
        "metadata-contract",
        body=(
            "<!-- task-session\n"
            "dependencies: 90A, 124C\n"
            "executable: true\n"
            "concurrency: independent-write\n"
            "owner_gate: explicit-launch\n"
            "integration: task-pr-to-dev\n"
            "-->"
        ),
    )
    controller = task_session.TaskController(
        git_repository, github=FakeGitHub(git_repository.ref("origin/dev"))
    )

    result = controller.validate_metadata()

    assert result["ok"] is True
    assert result["tasks"] == [
        {
            "task_id": "209",
            "canonical_task_path": str(
                (root / "codex-backlog" / "tasks" / "209-metadata-contract.md").resolve()
            ),
            "dependencies": ["90A", "124C"],
            "executable": True,
            "concurrency_class": "independent-write",
            "owner_gate": "explicit-launch",
            "integration_policy": "task-pr-to-dev",
            "metadata_source": "task-session-block",
        }
    ]


def test_adopt_current_recovers_single_existing_task_worktree(
    repository: tuple[Path, Any],
) -> None:
    root, _git_repository = repository
    task_path = _write_task(root, "210", "adopt-existing")
    worktree = root / ".artifacts" / "worktrees" / "task-210-adopt-existing"
    _git(root, "branch", "task/210-adopt-existing", "origin/dev")
    _git(root, "worktree", "add", str(worktree), "task/210-adopt-existing")
    adopted_repository = task_session.GitRepository(worktree)
    controller = task_session.TaskController(
        adopted_repository,
        github=FakeGitHub(adopted_repository.ref("origin/dev")),
    )

    lease = controller.adopt_current("210", owner_launch=True, session_label="pytest-adopt")

    assert lease["adopted_existing_session"] is True
    assert lease["worktree"] == str(worktree.resolve())
    assert lease["canonical_task_path"] == str(task_path.resolve())


def test_state_store_atomic_create_and_corruption_are_fail_closed(tmp_path: Path) -> None:
    store = task_session.StateStore(tmp_path / ".git")
    store.initialize()
    path = store.task_lease_path("127")
    store.create_json(path, {"task_id": "127"})
    with pytest.raises(task_session.TaskSessionError, match="already exists"):
        store.create_json(path, {"task_id": "127"})
    path.write_text("{broken", encoding="utf-8")
    with pytest.raises(task_session.TaskSessionError, match="Corrupted"):
        store.read_json(path)


def test_two_candidate_queue_only_allows_head_and_second_becomes_stale(
    repository: tuple[Path, Any],
) -> None:
    root, git_repository = repository
    base_sha = git_repository.ref("origin/dev")
    github = FakeGitHub(base_sha)
    controller = task_session.TaskController(git_repository, github=github)
    for number, task_id in ((1, "301"), (2, "302")):
        branch = f"task/{task_id}-synthetic-task"
        worktree = root / ".artifacts" / "worktrees" / f"synthetic-{task_id}"
        _git(root, "branch", branch, "origin/dev")
        _git(root, "worktree", "add", str(worktree), branch)
        (worktree / f"task-{task_id}.txt").write_text(f"Task {task_id}\n", encoding="utf-8")
        _git(worktree, "add", f"task-{task_id}.txt")
        _git(worktree, "commit", "-m", f"feat: [Task {task_id}] synthetic queue candidate")
        head_sha = _git(worktree, "rev-parse", "HEAD")
        _task_lease(controller, task_id, root, base_sha, ready_head_sha=head_sha)
        github.pulls[number] = _task_pr(number, task_id, base_sha, head_sha)
        github.commits[number] = [_task_commit(task_id)]
        github.checks[head_sha] = [_success_check(head_sha)]
        controller.enqueue_integration(task_id, pr_number=number)

    transcript: list[dict[str, Any]] = [
        {
            "event": "queued",
            "order": ["301", "302"],
            "base_sha": base_sha,
        }
    ]
    with pytest.raises(task_session.TaskSessionError, match="Only queue head") as blocked_second:
        controller.prepare_integration("302")
    transcript.append({"event": "second-blocked", "reason": str(blocked_second.value)})
    integration = controller.prepare_integration("301")
    assert integration["task_id"] == "301"
    transcript.append(
        {
            "event": "first-eligible",
            "task_id": integration["task_id"],
            "head_sha": integration["head_sha"],
        }
    )

    merge_sha = "c" * 40
    github.dev_sha = merge_sha
    github.pulls[1]["merged_at"] = "2026-01-01T00:00:00Z"
    github.pulls[1]["merge_commit_sha"] = merge_sha
    github.runs[merge_sha] = [
        {
            "id": 44,
            "event": "push",
            "head_branch": "dev",
            "head_sha": merge_sha,
            "status": "completed",
            "conclusion": "success",
        }
    ]
    completed = controller.complete_integration("301", merge_sha=merge_sha)
    transcript.append(
        {
            "event": "first-dev-ci-success",
            "task_id": completed["task_id"],
            "merge_sha": completed["merge_sha"],
        }
    )

    with pytest.raises(task_session.TaskSessionError, match="stale") as stale_second:
        controller.prepare_integration("302")
    transcript.append({"event": "second-stale", "reason": str(stale_second.value)})
    print(json.dumps(transcript, indent=2))


@pytest.mark.parametrize("conclusion", ["FAILURE", "CANCELLED", "TIMED_OUT"])
def test_non_success_exact_head_checks_never_grant_integration(
    repository: tuple[Path, Any], conclusion: str
) -> None:
    root, git_repository = repository
    base_sha = git_repository.ref("origin/dev")
    github = FakeGitHub(base_sha)
    controller = task_session.TaskController(git_repository, github=github)
    head_sha = "d" * 40
    _task_lease(controller, "303", root, base_sha, ready_head_sha=head_sha)
    github.pulls[3] = _task_pr(3, "303", base_sha, head_sha)
    github.commits[3] = [_task_commit("303")]
    github.checks[head_sha] = [
        {"name": "checks", "head_sha": head_sha, "status": "completed", "conclusion": conclusion}
    ]
    controller.enqueue_integration("303", pr_number=3)

    with pytest.raises(task_session.TaskSessionError, match="not successful"):
        controller.prepare_integration("303")


def test_release_lease_blocks_queue_and_integration(repository: tuple[Path, Any]) -> None:
    root, git_repository = repository
    base_sha = git_repository.ref("origin/dev")
    github = FakeGitHub(base_sha)
    controller = task_session.TaskController(git_repository, github=github)
    _task_lease(controller, "304", root, base_sha, ready_head_sha="e" * 40)
    controller.release_freeze("start", sha=base_sha, session_label="release-test")
    github.pulls[4] = _task_pr(4, "304", base_sha, "e" * 40)
    github.commits[4] = [_task_commit("304")]

    with pytest.raises(task_session.TaskSessionError, match="Release freeze"):
        controller.enqueue_integration("304", pr_number=4)


def test_prepare_integration_rechecks_release_lease_under_shared_lock(
    repository: tuple[Path, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    root, git_repository = repository
    base_sha = git_repository.ref("origin/dev")
    head_sha = "7" * 40
    github = FakeGitHub(base_sha)
    controller = task_session.TaskController(git_repository, github=github)
    _task_lease(controller, "307", root, base_sha, ready_head_sha=head_sha)
    github.pulls[7] = _task_pr(7, "307", base_sha, head_sha)
    github.commits[7] = [_task_commit("307")]
    github.checks[head_sha] = [_success_check(head_sha)]
    controller.enqueue_integration("307", pr_number=7)

    @contextmanager
    def inject_release_lease():
        task_session.StateStore.replace_json(
            controller.store.mode_lease_path("release"), {"mode": "release"}
        )
        yield

    monkeypatch.setattr(controller.store, "lock", inject_release_lease)

    with pytest.raises(task_session.TaskSessionError, match="acquired while integration"):
        controller.prepare_integration("307")
    assert not controller.store.mode_lease_path("integration").exists()


def test_release_freeze_rechecks_integration_lease_under_shared_lock(
    repository: tuple[Path, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    _, git_repository = repository
    controller = task_session.TaskController(
        git_repository, github=FakeGitHub(git_repository.ref("origin/dev"))
    )
    controller.store.initialize()

    @contextmanager
    def inject_integration_lease():
        task_session.StateStore.replace_json(
            controller.store.mode_lease_path("integration"), {"mode": "integration"}
        )
        yield

    monkeypatch.setattr(controller.store, "lock", inject_integration_lease)

    with pytest.raises(task_session.TaskSessionError, match="integration lease is active"):
        controller.release_freeze(
            "start", sha=git_repository.ref("origin/dev"), session_label="race-test"
        )
    assert not controller.store.mode_lease_path("release").exists()


def test_unmerged_integration_can_be_withdrawn_for_blocking_fix(
    repository: tuple[Path, Any],
) -> None:
    root, git_repository = repository
    base_sha = git_repository.ref("origin/dev")
    head_sha = "6" * 40
    github = FakeGitHub(base_sha)
    controller = task_session.TaskController(git_repository, github=github)
    _task_lease(controller, "308", root, base_sha, ready_head_sha=head_sha)
    github.pulls[8] = _task_pr(8, "308", base_sha, head_sha)
    github.commits[8] = [_task_commit("308")]
    github.checks[head_sha] = [_success_check(head_sha)]
    controller.enqueue_integration("308", pr_number=8)
    controller.prepare_integration("308")

    result = controller.withdraw_integration("308", reason="blocking review fix")

    assert result["withdrawn"]["state"] == "withdrawn-for-fix"
    assert result["task_lease"]["lifecycle_state"] == "implementation"
    assert "ready_head_sha" not in result["task_lease"]
    assert controller.store.read_json(controller.store.queue_path)["candidates"] == []
    assert not controller.store.mode_lease_path("integration").exists()


def test_queued_integration_can_be_withdrawn_before_checks_pass(
    repository: tuple[Path, Any],
) -> None:
    root, git_repository = repository
    base_sha = git_repository.ref("origin/dev")
    head_sha = "5" * 40
    github = FakeGitHub(base_sha)
    controller = task_session.TaskController(git_repository, github=github)
    _task_lease(controller, "309", root, base_sha, ready_head_sha=head_sha)
    github.pulls[9] = _task_pr(9, "309", base_sha, head_sha)
    github.commits[9] = [_task_commit("309")]
    controller.enqueue_integration("309", pr_number=9)

    result = controller.withdraw_integration("309", reason="failed required checks")

    assert result["withdrawn"]["state"] == "withdrawn-for-fix"
    assert result["task_lease"]["lifecycle_state"] == "implementation"
    assert "ready_head_sha" not in result["task_lease"]
    assert controller.store.read_json(controller.store.queue_path)["candidates"] == []
    assert not controller.store.mode_lease_path("integration").exists()


def test_research_readonly_lease_cannot_enter_integration_queue(
    repository: tuple[Path, Any],
) -> None:
    root, git_repository = repository
    base_sha = git_repository.ref("origin/dev")
    github = FakeGitHub(base_sha)
    controller = task_session.TaskController(git_repository, github=github)
    head_sha = "9" * 40
    _task_lease(
        controller,
        "305",
        root,
        base_sha,
        ready_head_sha=head_sha,
        mode="research-readonly",
    )
    github.pulls[5] = _task_pr(5, "305", base_sha, head_sha)
    github.commits[5] = [_task_commit("305")]

    with pytest.raises(task_session.TaskSessionError, match="Research-readonly"):
        controller.enqueue_integration("305", pr_number=5)


def test_complete_integration_requires_exact_leased_pr_merge(
    repository: tuple[Path, Any],
) -> None:
    root, git_repository = repository
    base_sha = git_repository.ref("origin/dev")
    github = FakeGitHub(base_sha)
    controller = task_session.TaskController(git_repository, github=github)
    head_sha = "8" * 40
    _task_lease(controller, "306", root, base_sha, ready_head_sha=head_sha)
    github.pulls[6] = _task_pr(6, "306", base_sha, head_sha)
    github.commits[6] = [_task_commit("306")]
    github.checks[head_sha] = [_success_check(head_sha)]
    controller.enqueue_integration("306", pr_number=6)
    controller.prepare_integration("306")
    unrelated_sha = "7" * 40
    github.dev_sha = unrelated_sha
    github.runs[unrelated_sha] = [
        {
            "id": 45,
            "event": "push",
            "head_branch": "dev",
            "head_sha": unrelated_sha,
            "status": "completed",
            "conclusion": "success",
        }
    ]

    with pytest.raises(task_session.TaskSessionError, match="exact merge result"):
        controller.complete_integration("306", merge_sha=unrelated_sha)


def test_dev_ruleset_validation_requires_pr_and_strict_aggregate_checks() -> None:
    weak = [
        {
            "target": "branch",
            "enforcement": "active",
            "conditions": {"ref_name": {"include": ["refs/heads/dev"]}},
            "rules": [{"type": "deletion"}, {"type": "non_fast_forward"}],
        }
    ]
    issues = task_session.validate_dev_ruleset(weak, expected_app_id=123)
    assert "dev Ruleset is missing pull_request" in issues
    assert "dev Ruleset is missing required_status_checks" in issues

    strict = [
        {
            "target": "branch",
            "enforcement": "active",
            "conditions": {"ref_name": {"include": ["refs/heads/dev"]}},
            "bypass_actors": [
                {"actor_type": "Integration", "actor_id": 123, "bypass_mode": "always"}
            ],
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
    assert task_session.validate_dev_ruleset(strict, expected_app_id=123) == []
    wrong_app = json.loads(json.dumps(strict))
    wrong_app[0]["bypass_actors"][0]["actor_id"] = 999
    assert "does not match deployed-sync App" in " ".join(
        task_session.validate_dev_ruleset(wrong_app, expected_app_id=123)
    )
    broad_bypass = json.loads(json.dumps(strict))
    broad_bypass[0]["bypass_actors"] = [
        {"actor_type": "RepositoryRole", "actor_id": 5, "bypass_mode": "always"}
    ]
    assert "dev Ruleset bypass must be one Integration actor in always mode" in (
        task_session.validate_dev_ruleset(broad_bypass, expected_app_id=123)
    )


def test_doctor_compares_tracking_origin_dev_with_live_github_head(
    repository: tuple[Path, Any],
) -> None:
    _, git_repository = repository
    github = FakeGitHub("f" * 40)
    controller = task_session.TaskController(git_repository, github=github)

    report = controller.doctor()

    assert any("local origin/dev is stale" in issue for issue in report["issues"])
    assert report["refs"]["live/dev"] == "f" * 40


def test_doctor_blocks_active_release_critical_workflow_even_without_release_lease(
    repository: tuple[Path, Any],
) -> None:
    _, git_repository = repository
    github = FakeGitHub(git_repository.ref("origin/dev"))
    github.ruleset_payload = [
        {
            "target": "branch",
            "enforcement": "active",
            "conditions": {"ref_name": {"include": ["refs/heads/dev"]}},
            "bypass_actors": [
                {"actor_type": "Integration", "actor_id": 123, "bypass_mode": "always"}
            ],
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
    github.active_runs = [
        {
            "id": 55,
            "name": "Deploy production",
            "event": "workflow_run",
            "head_branch": "master",
            "head_sha": "a" * 40,
            "status": "in_progress",
        }
    ]
    controller = task_session.TaskController(git_repository, github=github)

    report = controller.doctor()

    assert "active dev/master CI, deploy or sync run blocks mutation" in report["issues"]


def test_dev_provenance_accepts_task_merge_deployed_sync_and_approved_recovery() -> None:
    task_merge = {
        "number": 9,
        "title": "[Task 90A] Valid merge",
        "merged_at": "2026-01-01T00:00:00Z",
        "merge_commit_sha": "a" * 40,
        "base": {"ref": "dev"},
        "head": {"ref": "task/90A-valid-merge"},
    }
    assert (
        task_session.classify_dev_provenance(
            sha="a" * 40,
            master_sha="b" * 40,
            associated_pulls=[task_merge],
            deploy_runs=[],
        )["kind"]
        == "task-pr-merge"
    )
    assert (
        task_session.classify_dev_provenance(
            sha="b" * 40,
            master_sha="b" * 40,
            associated_pulls=[],
            deploy_runs=[
                {
                    "head_sha": "b" * 40,
                    "status": "completed",
                    "conclusion": "success",
                    "event": "workflow_run",
                }
            ],
        )["kind"]
        == "deployed-master-sync"
    )
    assert (
        task_session.classify_dev_provenance(
            sha="c" * 40,
            master_sha="b" * 40,
            associated_pulls=[],
            deploy_runs=[],
            approved_recovery_sha="c" * 40,
        )["kind"]
        == "owner-approved-recovery"
    )


def test_direct_feature_dev_update_is_not_release_eligible() -> None:
    with pytest.raises(task_session.TaskSessionError, match="Unauthorized dev update"):
        task_session.classify_dev_provenance(
            sha="f" * 40,
            master_sha="a" * 40,
            associated_pulls=[],
            deploy_runs=[],
        )


@pytest.mark.parametrize(
    "filename", [".artifacts/test.log", ".env.production", "deploy/private.key"]
)
def test_task_pr_forbids_artifacts_and_credential_paths(filename: str) -> None:
    with pytest.raises(task_session.TaskSessionError, match="forbidden"):
        task_session.validate_task_pull_request_files([{"filename": filename}])


def test_task_pr_accepts_complete_inventory_larger_than_one_api_page() -> None:
    files = [{"filename": f"assets/exercise-{index}.webp"} for index in range(169)]

    task_session.validate_task_pull_request_files(files, expected_count=169)


def test_task_pr_rejects_incomplete_paginated_inventory() -> None:
    files = [{"filename": f"assets/exercise-{index}.webp"} for index in range(100)]

    with pytest.raises(task_session.TaskSessionError, match="received 100 of 169"):
        task_session.validate_task_pull_request_files(files, expected_count=169)


def test_github_client_collects_every_task_pr_file_page(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = task_session.GitHubClient(object(), repo_slug="owner/repository")
    calls: list[str] = []

    def fake_api(endpoint: str) -> list[dict[str, str]]:
        calls.append(endpoint)
        if endpoint.endswith("page=1"):
            return [{"filename": f"assets/exercise-{index}.webp"} for index in range(100)]
        return [{"filename": f"assets/exercise-{index}.webp"} for index in range(100, 169)]

    monkeypatch.setattr(client, "api", fake_api)

    assert len(client.pull_request_files(101)) == 169
    assert calls == [
        "pulls/101/files?per_page=100&page=1",
        "pulls/101/files?per_page=100&page=2",
    ]


def test_recover_is_read_only_and_preserves_dirty_unique_task_state(
    repository: tuple[Path, Any],
) -> None:
    root, git_repository = repository
    _write_task(root, "401", "recover-me")
    controller = task_session.TaskController(
        git_repository, github=FakeGitHub(git_repository.ref("origin/dev"))
    )
    started = controller.start("401", owner_launch=True, session_label="pytest", offline=True)
    worktree = Path(started["lease"]["worktree"])
    (worktree / "unique.txt").write_text("unique\n", encoding="utf-8")
    _git(worktree, "add", "unique.txt")
    _git(worktree, "commit", "-m", "feat: [Task 401] unique recovery state")
    (worktree / "dirty.txt").write_text("dirty\n", encoding="utf-8")

    result = controller.recover("401")

    assert result["classification"] == "RECOVERY_REQUIRED"
    assert result["mutation_performed"] is False
    assert any(item["dirty"] for item in result["worktrees"])
    assert any(item["unique_commits"] for item in result["worktrees"])
    assert (worktree / "dirty.txt").exists()


def _prepare_finish_state(
    repository: tuple[Path, Any], task_id: str
) -> tuple[Any, Path, str, str, str]:
    root, git_repository = repository
    _write_task(root, task_id, "automatic-closeout")
    base_sha = git_repository.ref("origin/dev")
    controller = task_session.TaskController(git_repository, github=FakeGitHub(base_sha))
    started = controller.start(task_id, owner_launch=True, session_label="pytest", offline=True)
    worktree = Path(started["lease"]["worktree"])
    branch = str(started["lease"]["branch"])
    (worktree / "closeout.txt").write_text("merged task\n", encoding="utf-8")
    _git(worktree, "add", "closeout.txt")
    _git(worktree, "commit", "-m", f"[Task {task_id}] test: synthetic closeout")
    head_sha = _git(worktree, "rev-parse", "HEAD")
    _git(root, "merge", "--no-ff", branch, "-m", f"[Task {task_id}] merge synthetic task")
    merge_sha = _git(root, "rev-parse", "HEAD")
    _git(root, "branch", "-f", "master", merge_sha)
    _git(root, "push", "origin", "dev", "master")

    lease_path = controller.store.task_lease_path(task_id)
    lease = controller.store.read_json(lease_path)
    lease["lifecycle_state"] = "dev-ci-success"
    lease["ready_head_sha"] = head_sha
    controller.store.replace_json(lease_path, lease)
    controller.store.create_json(
        controller.store.history / f"task-{task_id}.json",
        {
            "task_id": task_id,
            "state": "dev-ci-success",
            "head_sha": head_sha,
            "merge_sha": merge_sha,
        },
    )
    return controller, worktree, branch, head_sha, merge_sha


def test_finish_removes_exact_clean_merged_worktree_and_local_branch(
    repository: tuple[Path, Any],
) -> None:
    controller, worktree, branch, _, _ = _prepare_finish_state(repository, "402")
    lease_path = controller.store.task_lease_path("402")

    result = controller.finish("402")

    assert result["cleanup_performed"] is True
    assert result["removed_worktree"] == str(worktree.resolve())
    assert result["deleted_local_branch"] == branch
    assert not worktree.exists()
    assert not controller.repository.ref_exists(branch)
    assert not lease_path.exists()
    history = controller.store.read_json(controller.store.history / "task-402.json")
    assert history["state"] == "finished"
    assert history["cleanup"]["branch"] == branch
    assert "cleanup_allowed_after_owner_confirmation" not in history


def test_finish_refuses_dirty_worktree_and_preserves_state(
    repository: tuple[Path, Any],
) -> None:
    controller, worktree, branch, _, _ = _prepare_finish_state(repository, "403")
    (worktree / "uncommitted.txt").write_text("preserve me\n", encoding="utf-8")

    with pytest.raises(task_session.TaskSessionError, match="refuses dirty task worktree"):
        controller.finish("403")

    assert worktree.is_dir()
    assert controller.repository.ref_exists(branch)
    assert controller.store.task_lease_path("403").exists()
    history = controller.store.read_json(controller.store.history / "task-403.json")
    assert history["state"] == "dev-ci-success"


def test_finish_refuses_unique_commits_and_preserves_state(
    repository: tuple[Path, Any],
) -> None:
    controller, worktree, branch, _, _ = _prepare_finish_state(repository, "404")
    (worktree / "unique.txt").write_text("preserve unique commit\n", encoding="utf-8")
    _git(worktree, "add", "unique.txt")
    _git(worktree, "commit", "-m", "[Task 404] test: preserve unique commit")
    unique_head = _git(worktree, "rev-parse", "HEAD")
    lease_path = controller.store.task_lease_path("404")
    lease = controller.store.read_json(lease_path)
    lease["ready_head_sha"] = unique_head
    controller.store.replace_json(lease_path, lease)
    history_path = controller.store.history / "task-404.json"
    history = controller.store.read_json(history_path)
    history["head_sha"] = unique_head
    controller.store.replace_json(history_path, history)

    with pytest.raises(task_session.TaskSessionError, match="unique commits"):
        controller.finish("404")

    assert worktree.is_dir()
    assert controller.repository.ref(branch) == unique_head
    assert lease_path.exists()


def test_finish_refuses_ambiguous_task_branch_and_worktree_state(
    repository: tuple[Path, Any],
) -> None:
    controller, worktree, branch, head_sha, _ = _prepare_finish_state(repository, "405")
    _git(controller.repository.current_worktree, "branch", "task/405-duplicate", head_sha)

    with pytest.raises(task_session.TaskSessionError, match="exactly one matching"):
        controller.finish("405")

    assert worktree.is_dir()
    assert controller.repository.ref_exists(branch)
    assert controller.repository.ref_exists("task/405-duplicate")
    assert controller.store.task_lease_path("405").exists()


def test_finish_refuses_unsynchronized_deployed_refs(
    repository: tuple[Path, Any],
) -> None:
    controller, worktree, branch, _, _ = _prepare_finish_state(repository, "406")
    previous_master = controller.repository.git("rev-parse", "origin/master^")
    controller.repository.git("update-ref", "refs/remotes/origin/master", previous_master)

    with pytest.raises(task_session.TaskSessionError, match="requires exact deployed"):
        controller.finish("406")

    assert worktree.is_dir()
    assert controller.repository.ref_exists(branch)
    assert controller.store.task_lease_path("406").exists()


def test_finish_refuses_cross_linked_or_non_terminal_history(
    repository: tuple[Path, Any],
) -> None:
    controller, worktree, branch, _, _ = _prepare_finish_state(repository, "407")
    history_path = controller.store.history / "task-407.json"
    history = controller.store.read_json(history_path)
    history["task_id"] = "999"
    controller.store.replace_json(history_path, history)

    with pytest.raises(task_session.TaskSessionError, match="history does not match"):
        controller.finish("407")

    assert worktree.is_dir()
    assert controller.repository.ref_exists(branch)
    assert controller.store.task_lease_path("407").exists()


def test_finish_refuses_execution_from_task_worktree(
    repository: tuple[Path, Any],
) -> None:
    controller, worktree, branch, _, _ = _prepare_finish_state(repository, "408")
    task_controller = task_session.TaskController(task_session.GitRepository(worktree))

    with pytest.raises(task_session.TaskSessionError, match="canonical dev worktree"):
        task_controller.finish("408")

    assert worktree.is_dir()
    assert controller.repository.ref_exists(branch)
    assert controller.store.task_lease_path("408").exists()
