from pathlib import Path
from types import SimpleNamespace

import pytest
from scripts import ci_contract


def test_ci_contract_is_valid_and_profiles_are_non_empty() -> None:
    ci_contract.validate_contract()
    assert ci_contract.contract_digest()
    assert all(ci_contract.PROFILE_GROUPS.values())


def test_profiles_reference_shared_command_groups() -> None:
    for groups in ci_contract.PROFILE_GROUPS.values():
        assert set(groups) <= set(ci_contract.COMMAND_GROUPS)


def test_commands_are_stable_and_have_unique_names() -> None:
    for spec in ci_contract.COMMAND_GROUPS.values():
        assert len({command.name for command in spec.commands}) == len(spec.commands)
        assert all(command.argv for command in spec.commands)


def test_contract_digest_changes_when_contract_changes(monkeypatch) -> None:
    original_digest = ci_contract.contract_digest()
    original = ci_contract.COMMAND_GROUPS["quality"]
    monkeypatch.setitem(
        ci_contract.COMMAND_GROUPS,
        "quality",
        ci_contract.GroupSpec(
            name=original.name,
            commands=(*original.commands, ci_contract.CommandSpec("sentinel", ("true",))),
            prerequisites=original.prerequisites,
        ),
    )
    assert ci_contract.contract_digest() != original_digest


def test_shards_parse_and_select_deterministically() -> None:
    assert ci_contract.parse_shard("1/4") == (0, 4)
    assert ci_contract.parse_shard("4/4") == (3, 4)
    nodes = tuple(f"test_{index}" for index in range(8))
    assert ci_contract.select_shard(nodes, shard_index=0, shard_count=4) == (
        "test_0",
        "test_4",
    )
    assert ci_contract.select_shard(nodes, shard_index=3, shard_count=4) == (
        "test_3",
        "test_7",
    )
    with pytest.raises(ci_contract.CIContractError):
        ci_contract.parse_shard("5/4")


def test_python_node_normalization_preserves_escaped_parameter_ids() -> None:
    assert (
        ci_contract._normalize_python_test_node(
            r"backend\tests\test_app.py::test_public_content[\u041e]"
        )
        == r"backend/tests/test_app.py::test_public_content[\u041e]"
    )


def test_frontend_e2e_shard_is_forwarded_to_playwright(monkeypatch, tmp_path: Path) -> None:
    calls: list[list[str]] = []
    monkeypatch.setattr(
        ci_contract,
        "missing_prerequisites",
        lambda group, *, root, env: [],
    )

    def fake_run(argv, **kwargs):
        del kwargs
        calls.append(list(argv))
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(ci_contract.subprocess, "run", fake_run)
    ci_contract.run_group("frontend-e2e", root=tmp_path, env={}, shard="2/4")

    assert calls[0][-2:] == ["--", "--shard=2/4"]


def test_python_shard_collects_and_runs_only_its_node_ids(monkeypatch, tmp_path: Path) -> None:
    calls: list[list[str]] = []
    monkeypatch.setattr(
        ci_contract,
        "missing_prerequisites",
        lambda group, *, root, env: [],
    )
    collected = "\n".join(
        [
            "backend/tests/test_a.py::test_a",
            "backend/tests/test_b.py::test_b",
            "bot/tests/test_c.py::test_c",
            "bot/tests/test_d.py::test_d",
            "backend/tests/test_e.py::test_e",
            "bot/tests/test_f.py::test_f",
        ]
    )

    def fake_run(argv, **kwargs):
        calls.append(list(argv))
        if "--collect-only" in argv:
            return SimpleNamespace(returncode=0, stdout=collected, stderr="")
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(ci_contract.subprocess, "run", fake_run)
    ci_contract.run_group(
        "python-tests",
        root=tmp_path,
        env={"TEST_DATABASE_URL": "postgresql://test"},
        shard="2/4",
    )

    assert calls[1][-2:] == ["--collect-only", "-q"]
    assert calls[2][2:4] == [
        "backend/tests/test_b.py::test_b",
        "bot/tests/test_f.py::test_f",
    ]


def test_windows_node_commands_use_cmd_wrappers(monkeypatch) -> None:
    monkeypatch.setattr(ci_contract.os, "name", "nt")
    assert ci_contract._resolve_argv(("npm", "run", "test"))[0] == "npm.cmd"
    assert ci_contract._resolve_argv(("npx", "vite", "build"))[0] == "npx.cmd"


def test_migrations_use_the_selected_python_interpreter() -> None:
    commands = ci_contract.COMMAND_GROUPS["migrated-stack"].commands
    assert commands[0].argv[:3] == ("python", "-m", "alembic")
    assert commands[1].argv[:3] == ("python", "-m", "alembic")


def test_workflow_calls_group_entrypoint_instead_of_inline_command_copy() -> None:
    root = Path(__file__).parents[1]
    workflow = (root / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    for group in (
        "quality",
        "policy",
        "frontend-checks",
        "frontend-e2e",
        "python-tests",
        "migrated-stack",
        "dependency-audit",
        "container-contract",
    ):
        assert f"scripts/ci_contract.py run-group {group}" in workflow
    assert "npm run typecheck" not in workflow
    assert "npm run e2e:ci" not in workflow
    assert "scripts/run_pytest.py backend/tests" not in workflow


def test_workflow_keeps_four_way_smoke_and_python_shards_independent() -> None:
    root = Path(__file__).parents[1]
    workflow = (root / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

    assert "name: Frontend smoke (${{ matrix.shard }}/4)" in workflow
    assert "name: Python tests (${{ matrix.shard }}/4)" in workflow
    assert workflow.count("        shard: [1, 2, 3, 4]") == 2
    assert 'run-group frontend-e2e --shard "${{ matrix.shard }}/4"' in workflow
    assert 'run-group python-tests --shard "${{ matrix.shard }}/4"' in workflow
    assert workflow.count("          path: ~/.cache/ms-playwright") == 2
    assert (
        workflow.count(
            "          key: playwright-${{ runner.os }}-${{ hashFiles('frontend/package-lock.json') }}"
        )
        == 2
    )
    assert (
        "  frontend-smoke:\n    name: Frontend smoke (${{ matrix.shard }}/4)\n    if:" in workflow
    )
    assert "  migrated-stack:\n    name: Migrated PostgreSQL stack\n    if:" in workflow


def test_cross_stack_profile_includes_delivery_policy_gates() -> None:
    groups = set(ci_contract.PROFILE_GROUPS["cross-stack"])
    assert {"policy", "workflow-config", "deployment-contract"} <= groups
