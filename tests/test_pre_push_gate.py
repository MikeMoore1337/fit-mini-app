import json
from pathlib import Path

import pytest
from scripts import pre_push_gate


def test_scope_classification_is_deterministic() -> None:
    assert pre_push_gate.classify_scope(["frontend/src/App.tsx"])["profile"] == "frontend"
    assert pre_push_gate.classify_scope(["backend/fitminiapp_api/main.py"])["profile"] == "backend"
    assert (
        pre_push_gate.classify_scope([".github/workflows/ci.yml"])["profile"] == "workflow-platform"
    )
    assert pre_push_gate.classify_scope(["docs/release-flow.md"])["profile"] == "documentation"
    assert (
        pre_push_gate.classify_scope(["frontend/src/App.tsx", "backend/app.py"])["profile"]
        == "cross-stack"
    )


def test_scope_classification_is_conservative_for_unknown_files() -> None:
    assert pre_push_gate.classify_scope(["unknown/build-input.bin"])["profile"] == "cross-stack"


def test_current_pass_rejects_head_base_and_contract_drift(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    common = tmp_path / ".git"
    common.mkdir()
    context = pre_push_gate.RepositoryContext(
        root=tmp_path,
        common_dir=common,
        branch="task/135-gate",
        head_sha="a" * 40,
        task_id="135",
        base_sha="b" * 40,
        lease={},
    )
    path = pre_push_gate.evidence_path(context)
    path.parent.mkdir(parents=True)
    payload = {
        "evidence_version": 1,
        "contract_version": pre_push_gate.CONTRACT_VERSION,
        "terminal_result": "PRE_PUSH_CI_PASS",
        "head_sha": "a" * 40,
        "base_sha": "b" * 40,
        "branch": "task/135-gate",
        "task_id": "135",
        "target_base_branch": "master",
        "contract_digest": pre_push_gate.contract_digest(),
        "clean_worktree": True,
        "started_at": "2026-09-03T10:00:00Z",
        "finished_at": "2026-09-03T10:01:00Z",
        "gates": [{"group": "quality", "applicable": True, "status": "SUCCESS"}],
    }
    payload["evidence_digest"] = pre_push_gate._evidence_digest(payload)
    path.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr(pre_push_gate, "_status", lambda root: [])
    assert pre_push_gate.current_pass(context) is not None
    drifted = context.__class__(**{**context.__dict__, "head_sha": "c" * 40})
    assert pre_push_gate.current_pass(drifted) is None


def test_load_context_requires_master_base_in_lease(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        pre_push_gate,
        "_git_root",
        lambda root: (tmp_path, tmp_path / ".git"),
    )
    monkeypatch.setattr(pre_push_gate, "_branch", lambda root: "task/135-gate")
    monkeypatch.setattr(
        pre_push_gate,
        "_load_lease",
        lambda common, task: {
            "task_id": "135",
            "branch": "task/135-gate",
            "worktree": str(tmp_path),
            "canonical_task_path": str(tmp_path / "135-gate.md"),
        },
    )
    (tmp_path / "135-gate.md").write_text("# [Task 135] gate\n", encoding="utf-8")
    monkeypatch.setattr(pre_push_gate, "_head", lambda root: "a" * 40)
    with pytest.raises(pre_push_gate.GateError, match="no lease-bound master base"):
        pre_push_gate.load_context(tmp_path)
