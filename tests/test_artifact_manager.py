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
        "OUTPUT = '.artifacts/new-ad-hoc/output.json'\n", encoding="utf-8"
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
