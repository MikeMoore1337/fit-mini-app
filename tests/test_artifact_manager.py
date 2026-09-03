from __future__ import annotations

import importlib.util
import json
import os
import sys
from datetime import timedelta
from pathlib import Path

import pytest


def _load_module():
    script = Path(__file__).parents[1] / "scripts" / "artifact_manager.py"
    spec = importlib.util.spec_from_file_location("artifact_manager", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


artifact_manager = _load_module()


def _manager(tmp_path: Path):
    return artifact_manager.ArtifactManager(tmp_path / ".artifacts")


def test_safe_relative_rejects_traversal_and_reparse_points(tmp_path: Path) -> None:
    manager = _manager(tmp_path)
    manager.ensure_layout("133")
    with pytest.raises(artifact_manager.ArtifactSafetyError):
        artifact_manager._safe_relative(manager.root, "../outside.txt")

    outside = tmp_path / "outside"
    outside.mkdir()
    link = manager.root / "runtime" / "link"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError) as error:
        pytest.skip(f"symlink creation unavailable: {error}")
    with pytest.raises(artifact_manager.ArtifactSafetyError, match="Reparse point"):
        artifact_manager._safe_relative(manager.root, "runtime/link/file.txt")


def test_allocate_writes_task_manifest_and_rejects_wrong_task_class(tmp_path: Path) -> None:
    manager = _manager(tmp_path)
    target = manager.allocate_directory(
        "133",
        "temporary",
        "temporary/run-1",
        purpose="test output",
        command="pytest",
        owner="test",
    )
    assert target.is_dir()
    manifest = json.loads(
        (manager.root / "tasks" / "133" / "manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["task_id"] == "133"
    assert manifest["entries"][0]["classification"] == "temporary"
    assert manager.validate(task_id="133")["ok"]
    with pytest.raises(artifact_manager.ArtifactError, match="must begin"):
        manager.allocate(
            "133",
            "evidence",
            "temporary/wrong-class",
            purpose="bad",
            command="test",
        )


def test_cli_allocate_records_provenance_command(tmp_path: Path, capsys) -> None:
    root = tmp_path / ".artifacts"

    exit_code = artifact_manager.main(
        [
            "--root",
            str(root),
            "allocate",
            "133",
            "temporary",
            "temporary/cli-run",
            "--purpose",
            "CLI test",
            "--command",
            "pytest -q",
            "--directory",
        ]
    )

    assert exit_code == 0
    assert "cli-run" in capsys.readouterr().out
    manifest = json.loads((root / "tasks" / "133" / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["entries"][0]["command"] == "pytest -q"


def test_cleanup_task_is_exact_idempotent_and_preserves_evidence(tmp_path: Path) -> None:
    manager = _manager(tmp_path)
    temporary = manager.allocate_directory(
        "133",
        "temporary",
        "temporary/run-1",
        purpose="test output",
        command="pytest",
    )
    (temporary / "generated.txt").write_text("reproducible\n", encoding="utf-8")
    evidence = manager.allocate(
        "133",
        "evidence",
        "evidence/selected.json",
        purpose="selected evidence",
        command="pytest",
    )
    evidence.write_text("keep\n", encoding="utf-8")

    result = manager.cleanup_task("133", terminal_state="finished")
    assert result["status"] == "completed"
    assert result["removed_count"] == 1
    assert not (temporary / "generated.txt").exists()
    assert evidence.exists()
    second = manager.cleanup_task("133", terminal_state="finished")
    assert second["status"] == "completed"
    assert second["removed_count"] == 0


def test_cleanup_task_blocks_non_terminal_target_lease(tmp_path: Path) -> None:
    manager = _manager(
        tmp_path,
    )
    state = tmp_path / "state"
    (state / "leases").mkdir(parents=True)
    (state / "leases" / "task-133.json").write_text(
        json.dumps({"task_id": "133", "mode": "write", "lifecycle_state": "implementation"}),
        encoding="utf-8",
    )
    manager.controller_state_dir = state
    target = manager.allocate_directory(
        "133",
        "temporary",
        "temporary/run",
        purpose="active output",
        command="test",
    )
    (target / "open.txt").write_text("keep\n", encoding="utf-8")
    result = manager.cleanup_task("133", terminal_state="finished")
    assert result["status"] == "blocked"
    assert (target / "open.txt").exists()
    assert result["cleanup_errors"]
    assert result["preserved"] == ["tasks/133/temporary/run/open.txt"]


def test_shared_cleanup_blocks_parallel_lease_and_unfinished_task_132(tmp_path: Path) -> None:
    manager = _manager(tmp_path)
    state = tmp_path / "state"
    (state / "leases").mkdir(parents=True)
    (state / "history").mkdir()
    (state / "leases" / "task-134.json").write_text(
        json.dumps({"task_id": "134", "mode": "write", "lifecycle_state": "implementation"}),
        encoding="utf-8",
    )
    (state / "history" / "task-132.json").write_text(
        json.dumps({"state": "integration"}), encoding="utf-8"
    )
    manager.controller_state_dir = state
    runtime = manager.root / "runtime" / "cache"
    runtime.mkdir(parents=True, exist_ok=True)
    target = runtime / "cache.bin"
    target.write_bytes(b"cache")

    plan = manager.dry_run()

    assert plan["summary"]["counts"]["DELETE"] == 0
    assert any("active task leases" in issue for issue in plan["safety"]["issues"])
    assert any("Task 132" in issue for issue in plan["safety"]["issues"])
    with pytest.raises(artifact_manager.ArtifactSafetyError, match="Cleanup blocked"):
        manager.apply_plan(plan, approved_plan_sha256=plan["plan_sha256"])


def test_dry_run_apply_requires_exact_unchanged_plan_and_is_idempotent(tmp_path: Path) -> None:
    manager = _manager(tmp_path)
    runtime = manager.root / "cache"
    runtime.mkdir(parents=True)
    target = runtime / "cache.bin"
    target.write_bytes(b"cache")
    plan = manager.dry_run()
    assert plan["plan_sha256"]
    with pytest.raises(artifact_manager.ArtifactSafetyError, match="owner-approved"):
        manager.apply_plan(plan, approved_plan_sha256=None)
    changed = target.with_name("cache-changed.bin")
    target.replace(changed)
    with pytest.raises(artifact_manager.ArtifactSafetyError, match="drift"):
        manager.apply_plan(plan, approved_plan_sha256=plan["plan_sha256"])

    fresh = manager.dry_run()
    result = manager.apply_plan(fresh, approved_plan_sha256=fresh["plan_sha256"])
    assert result["status"] == "completed"
    assert not changed.exists()
    repeat = manager.apply_plan(fresh, approved_plan_sha256=fresh["plan_sha256"])
    assert repeat["status"] == "completed"


def test_validate_detects_new_top_level_and_source_path(tmp_path: Path) -> None:
    manager = _manager(tmp_path)
    (manager.root / "new-ad-hoc").mkdir(parents=True)
    manager.repo_root.mkdir(parents=True, exist_ok=True)
    scripts = manager.repo_root / "scripts"
    scripts.mkdir()
    (scripts / "producer.py").write_text(
        "OUTPUT = '.artifacts/' + 'new-ad-hoc/output.json'\n", encoding="utf-8"
    )
    result = manager.validate()
    assert not result["ok"]
    assert any("new-ad-hoc" in error for error in result["errors"])


def test_runtime_cleanup_is_bounded_and_requires_plan_hash(tmp_path: Path) -> None:
    manager = _manager(tmp_path)
    old = manager.root / "runtime" / "cache"
    old.mkdir(parents=True)
    target = old / "old.bin"
    target.write_bytes(b"old")
    timestamp = target.stat().st_mtime - 10_000
    os.utime(target, (timestamp, timestamp))
    plan = manager.cleanup_runtime(ttl=timedelta(seconds=1), max_entries=1, max_bytes=10)
    assert plan["summary"]["counts"]["DELETE"] == 1
    with pytest.raises(artifact_manager.ArtifactSafetyError):
        manager.cleanup_runtime(
            ttl=timedelta(seconds=1),
            max_entries=1,
            max_bytes=10,
            apply=True,
            approved_plan_sha256="wrong",
        )
    result = manager.cleanup_runtime(
        ttl=timedelta(seconds=1),
        max_entries=1,
        max_bytes=10,
        apply=True,
        approved_plan_sha256=plan["plan_sha256"],
    )
    assert result["status"] == "completed"


def test_ensure_layout_refuses_canonical_reparse_point(tmp_path: Path) -> None:
    manager = _manager(tmp_path)
    manager.root.mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    link = manager.root / "runtime"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError) as error:
        pytest.skip(f"symlink creation unavailable: {error}")

    with pytest.raises(artifact_manager.ArtifactSafetyError, match="Reparse point"):
        manager.ensure_layout()


def test_manifest_validation_rejects_unregistered_durable_artifact(tmp_path: Path) -> None:
    manager = _manager(tmp_path)
    manager.ensure_layout("133")
    durable = manager.root / "tasks" / "133" / "evidence" / "unregistered.json"
    durable.write_text("{}\n", encoding="utf-8")

    result = manager.validate(task_id="133")

    assert not result["ok"]
    assert any("unregistered.json" in error for error in result["errors"])


def test_audit_keeps_worktrees_and_operations_protected(tmp_path: Path) -> None:
    manager = _manager(tmp_path)
    manager.ensure_layout()
    worktree_file = manager.root / "worktrees" / "registered" / "file.bin"
    backup_file = manager.root / "operations" / "backups" / "database.dump"
    worktree_file.parent.mkdir(parents=True)
    backup_file.parent.mkdir(parents=True, exist_ok=True)
    worktree_file.write_bytes(b"worktree")
    backup_file.write_bytes(b"backup")

    entries = manager.audit()["entries"]

    by_path = {entry["path"]: entry for entry in entries}
    assert by_path["worktrees/registered/file.bin"]["disposition"] == "KEEP"
    assert by_path["operations/backups/database.dump"]["disposition"] == "KEEP"


def test_cleanup_task_counts_only_selected_scope(tmp_path: Path) -> None:
    manager = _manager(tmp_path)
    worker = manager.allocate_directory(
        "133",
        "temporary",
        "temporary/worker",
        purpose="worker output",
        command="test",
    )
    delivery = manager.allocate_directory(
        "133",
        "temporary",
        "temporary/delivery",
        purpose="delivery output",
        command="test",
    )
    worker_file = worker / "worker.bin"
    delivery_file = delivery / "delivery.bin"
    worker_file.write_bytes(b"worker")
    delivery_file.write_bytes(b"delivery")

    result = manager.cleanup_task(
        "133", terminal_state="finished", exclude_prefixes=("temporary/delivery",)
    )

    assert result["status"] == "completed"
    assert result["removed_bytes"] == len(b"worker")
    assert delivery_file.exists()


def test_cleanup_task_stops_on_target_drift(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manager = _manager(tmp_path)
    temporary = manager.allocate_directory(
        "133",
        "temporary",
        "temporary/worker",
        purpose="worker output",
        command="test",
    )
    target = temporary / "generated.bin"
    target.write_bytes(b"original")
    original_fingerprint = artifact_manager._file_fingerprint

    def change_before_fingerprint(path: Path) -> dict[str, object]:
        if path == target:
            target.write_bytes(b"changed")
        return original_fingerprint(path)

    monkeypatch.setattr(artifact_manager, "_file_fingerprint", change_before_fingerprint)
    drift = manager.cleanup_task("133", terminal_state="finished")
    assert drift["status"] == "partial-failure"
    assert drift["cleanup_errors"]
    assert target.exists()


def test_runtime_cleanup_applies_the_saved_exact_plan(tmp_path: Path) -> None:
    manager = _manager(tmp_path)
    target = manager.root / "runtime" / "cache" / "old.bin"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(b"old")
    old_timestamp = target.stat().st_mtime - 10_000
    os.utime(target, (old_timestamp, old_timestamp))

    plan = manager.cleanup_runtime(ttl=timedelta(seconds=1), max_entries=1, max_bytes=10)
    result = manager.cleanup_runtime(
        ttl=timedelta(seconds=1),
        max_entries=1,
        max_bytes=10,
        apply=True,
        approved_plan_sha256=plan["plan_sha256"],
        plan=plan,
    )

    assert result["status"] == "completed"
    assert not target.exists()
