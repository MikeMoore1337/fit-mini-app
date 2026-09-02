from pathlib import Path

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


def test_workflow_calls_group_entrypoint_instead_of_inline_command_copy() -> None:
    root = Path(__file__).parents[1]
    workflow = (root / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    for group in (
        "quality",
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
