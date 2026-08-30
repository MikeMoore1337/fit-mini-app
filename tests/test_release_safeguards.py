from pathlib import Path


def _release_policy_sources() -> tuple[str, str, str]:
    root = Path(__file__).resolve().parents[1]
    return (
        (root / "AGENTS.md").read_text(encoding="utf-8"),
        (root / "codex-backlog" / "GLOBAL_RULES.md").read_text(encoding="utf-8"),
        (root / "codex-backlog" / "TASK_EXECUTION_LIFECYCLE.md").read_text(encoding="utf-8"),
    )


def test_automated_deploy_keeps_revision_provenance_and_stale_run_guards() -> None:
    root = Path(__file__).resolve().parents[1]
    ci_workflow = (root / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    deploy_workflow = (root / ".github" / "workflows" / "deploy.yml").read_text(encoding="utf-8")
    deploy_script = (root / "scripts" / "deploy_production.sh").read_text(encoding="utf-8")

    assert "org.opencontainers.image.revision=${{ github.sha }}" in ci_workflow
    assert "workflow_dispatch:" not in deploy_workflow
    assert "pull-requests: read" in deploy_workflow
    assert '"repos/$REPOSITORY/commits/$DEPLOY_SHA/pulls"' in deploy_workflow
    assert '.merged_at != null and .base.ref == \\"master\\"' in deploy_workflow
    assert '.merge_commit_sha == \\"$DEPLOY_SHA\\"' in deploy_workflow
    assert deploy_workflow.index("Verify merged pull request provenance") < deploy_workflow.index(
        "Configure production SSH access"
    )
    assert "LATEST_MASTER_SHA=\\$(git rev-parse origin/master)" in deploy_workflow
    assert deploy_workflow.index("LATEST_MASTER_SHA=") < deploy_workflow.index(
        "git reset --hard '$DEPLOY_SHA'"
    )
    assert "Skipping superseded deployment" in deploy_workflow
    assert "if [ \\\"\\$LATEST_MASTER_SHA\\\" != '$DEPLOY_SHA' ]; then" in deploy_workflow
    assert (
        'echo \\"Skipping superseded deployment: tested revision $DEPLOY_SHA '
        'is no longer master head (\\$LATEST_MASTER_SHA)\\"' in deploy_workflow
    )

    assert "for attempt in 1 2 3 4 5; do" in deploy_workflow
    assert "GHCR login failed after 5 attempts" in deploy_workflow
    assert "_pull_images_with_retry" in (root / "scripts" / "zero_downtime_deploy.py").read_text(
        encoding="utf-8"
    )

    assert "PROD_ROLLOUT_MODE: single-slot" in deploy_workflow
    assert "DEPLOY_SINGLE_SLOT_CONFIRMED_SHA='$DEPLOY_SHA'" in deploy_workflow
    assert "'$PROD_ROLLOUT_MODE'" in deploy_workflow
    assert deploy_workflow.index("LATEST_MASTER_SHA=") < deploy_workflow.index(
        "DEPLOY_SINGLE_SLOT_CONFIRMED_SHA="
    )

    assert "scripts/zero_downtime_deploy.py" in deploy_script
    assert 'ROLLOUT_MODE="${4:-zero-downtime}"' in deploy_script
    assert "single-slot" in deploy_script
    assert "DEPLOY_SINGLE_SLOT_CONFIRMED_SHA" in (
        root / "scripts" / "zero_downtime_deploy.py"
    ).read_text(encoding="utf-8")
    assert "docker compose config --quiet" in deploy_script
    assert "--remove-orphans" not in deploy_script
    assert "docker compose up" not in deploy_script


def test_dev_runs_ci_but_cannot_publish_or_deploy_production() -> None:
    root = Path(__file__).resolve().parents[1]
    ci_workflow = (root / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    deploy_workflow = (root / ".github" / "workflows" / "deploy.yml").read_text(encoding="utf-8")

    assert "branches: [dev, master]" in ci_workflow
    assert "branches: [main, master]" not in ci_workflow
    assert ci_workflow.count("github.ref == 'refs/heads/master'") == 2
    assert ci_workflow.count("github.ref == 'refs/heads/dev'") == 1
    assert "Validate exact dev update provenance" in ci_workflow
    assert "branches: [master]" in deploy_workflow
    assert "branches: [dev" not in deploy_workflow
    assert "workflow_dispatch:" not in deploy_workflow


def test_release_pr_requires_completed_exact_sha_push_ci_and_serial_execution() -> None:
    root = Path(__file__).resolve().parents[1]
    ci_workflow = (root / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

    concurrency_lines = ci_workflow.split("\nconcurrency:\n", maxsplit=1)[1].split(
        "\nenv:\n", maxsplit=1
    )[0]
    concurrency_keys = {
        line.strip().split(":", maxsplit=1)[0]
        for line in concurrency_lines.splitlines()
        if line.startswith("  ") and not line.lstrip().startswith("#")
    }

    assert "actions: read" in ci_workflow
    assert "pull-requests: read" in ci_workflow
    assert "types: [opened, reopened, ready_for_review, synchronize]" in ci_workflow
    assert "&& 'dev-release' || github.ref" in ci_workflow
    assert "cancel-in-progress: false" in ci_workflow
    assert concurrency_keys == {"group", "cancel-in-progress"}
    assert "release-sequence:" in ci_workflow
    assert "Require successful push CI before release PR" in ci_workflow
    assert '"repos/$GITHUB_REPOSITORY/actions/workflows/ci.yml/runs"' in ci_workflow
    assert "-f event=push" in ci_workflow
    assert '-f head_sha="$HEAD_SHA"' in ci_workflow
    assert "-f status=success" in ci_workflow
    assert "PR_GATE_AT: ${{ github.event.pull_request.updated_at }}" in ci_workflow
    assert "PR_NUMBER: ${{ github.event.pull_request.number }}" in ci_workflow
    assert '"repos/$GITHUB_REPOSITORY/pulls/$PR_NUMBER"' in ci_workflow
    assert 'if [ "$current_pr_head" != "$HEAD_SHA" ]; then' in ci_workflow
    assert "Release sequence violation: stale PR event head" in ci_workflow
    assert "github.event.pull_request.head.repo.full_name == github.repository" in ci_workflow
    assert r".updated_at <= \"$PR_GATE_AT\"" in ci_workflow
    assert ci_workflow.count("needs: [release-sequence, task-provenance]") == 7
    assert "task-provenance:" in ci_workflow
    assert "TASK_PROVENANCE_RESULT: ${{ needs.task-provenance.result }}" in ci_workflow
    assert "RELEASE_SEQUENCE_RESULT: ${{ needs.release-sequence.result }}" in ci_workflow
    assert 'test "$RELEASE_SEQUENCE_RESULT" = success' in ci_workflow
    assert "github.event_name == 'pull_request' && 'checks' || 'branch-checks'" in ci_workflow


def test_auto_release_contract_is_fail_closed_for_medium_and_human_gates() -> None:
    agents, global_rules, lifecycle = _release_policy_sources()

    for source in (agents, global_rules, lifecycle):
        assert "AUTO_RELEASE_ELIGIBLE" in source
        assert "master" in source

    assert "dev ->" in global_rules
    assert "dev ->" in lifecycle
    assert "незакрытых `BLOCKER`, `HIGH` и `MEDIUM` ровно ноль" in lifecycle
    assert "явно обязательный owner checkpoint/approve, human/device evidence" in lifecycle
    assert "failure/rollback/manual-intervention verdict" in lifecycle.lower()
    assert "Direct push в `master` запрещён" in global_rules
    assert "expected PR head SHA" in lifecycle
    assert "required check `checks`" in lifecycle
    assert "fast-forward/sync `dev`" in lifecycle


def test_task127_global_auto_continue_contract_has_no_implicit_wait() -> None:
    agents, global_rules, lifecycle = _release_policy_sources()
    sources = (agents, global_rules, lifecycle)
    exact_contract = (
        "Если текущая task не объявляет `OWNER_CHECKPOINT`, `HUMAN_EVIDENCE`, "
        "`MANUAL_VISUAL_APPROVAL`,\n"
        "`LEGAL_COUNSEL_REQUIRED`, `EXTERNAL_AUTHORIZATION`, `DESTRUCTIVE_ACTION` или terminal "
        "blocker,\n"
        "controller/lifecycle после terminal success автоматически продолжает применимые review, "
        "QA,\n"
        "commit, task PR, serial integration, `dev` CI и normal release без дополнительного owner "
        "prompt.\n"
        "Тишина владельца не является gate. Следующая product task автоматически не запускается."
    )

    for source in sources:
        assert "terminal success" in source
        assert "не жд" in source or "не ждать" in source or "without waiting" in source
        assert exact_contract in source
    assert "do not start the next task automatically" in agents
    assert "Следующая product task автоматически не запускается" in global_rules
    assert "Не переходить к следующей task автоматически" in lifecycle

    assert "Один executable task-файл = одна Codex-сессия = одна" in global_rules
    assert "не ждёт дополнительного owner prompt" in global_rules
    assert "integration-only" in agents
    assert "serial merge в `dev`" in global_rules


def test_task_pr_dev_provenance_and_deployed_master_sync_contract() -> None:
    root = Path(__file__).resolve().parents[1]
    ci_workflow = (root / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    sync_workflow = (root / ".github" / "workflows" / "sync-dev-after-deploy.yml").read_text(
        encoding="utf-8"
    )
    controller = (root / "scripts" / "task_session.py").read_text(encoding="utf-8")

    assert "Task provenance" in ci_workflow
    assert "validate-pr --event" in ci_workflow
    assert "verify-dev-provenance --sha" in ci_workflow
    assert "github.event_name == 'push' && github.ref == 'refs/heads/dev'" in ci_workflow
    assert "github.event_name == 'push' && github.ref == 'refs/heads/master'" in ci_workflow
    assert "Task pull request base must be dev" in controller
    assert "Unauthorized dev update" in controller
    assert "Only queue head may integrate" in controller
    assert "Exact-head required check 'checks'" in controller

    assert "workflows: [Deploy production]" in sync_workflow
    assert "workflow_dispatch:" not in sync_workflow
    assert "ENABLE_DEPLOYED_MASTER_DEV_SYNC == 'true'" in sync_workflow
    assert (
        "actions/create-github-app-token@fee1f7d63c2ff003460e3d139729b119787bc349" in sync_workflow
    )
    assert 'if [ "$master_sha" != "$DEPLOY_SHA" ]; then' in sync_workflow
    assert 'git merge-base --is-ancestor "$dev_sha" "$DEPLOY_SHA"' in sync_workflow
    assert 'git push origin "$DEPLOY_SHA:refs/heads/dev"' in sync_workflow
    assert "force" not in sync_workflow.lower()


def test_task_ci_does_not_publish_or_start_production_deploy() -> None:
    root = Path(__file__).resolve().parents[1]
    ci_workflow = (root / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    deploy_workflow = (root / ".github" / "workflows" / "deploy.yml").read_text(encoding="utf-8")

    assert "if: github.event_name == 'push' && github.ref == 'refs/heads/master'" in ci_workflow
    assert ci_workflow.count("github.ref == 'refs/heads/master'") == 2
    assert "workflows: [CI]" in deploy_workflow
    assert "branches: [master]" in deploy_workflow
    assert "branches: [dev" not in deploy_workflow


def test_compact_first_contract_is_canonical() -> None:
    root = Path(__file__).resolve().parents[1]
    plain_language = (root / "codex-backlog" / "PLAIN_LANGUAGE_UX.md").read_text(encoding="utf-8")

    assert "COMPACT_FIRST_UX_CONTRACT.md" in plain_language
    assert "Primary action" in plain_language
    assert "максимум один уровень disclosure" in plain_language
    assert "aria-expanded" in plain_language


def test_slot_topology_keeps_gateway_stable_and_consumers_single_owner() -> None:
    root = Path(__file__).resolve().parents[1]
    compose = (root / "docker-compose.yml").read_text(encoding="utf-8")
    edge = (root / "deploy" / "Caddyfile.edge").read_text(encoding="utf-8")
    orchestrator = (root / "scripts" / "zero_downtime_deploy.py").read_text(encoding="utf-8")

    assert "backend-blue:" in compose and "backend-green:" in compose
    assert "worker-blue:" in compose and "worker-green:" in compose
    assert "bot-blue:" in compose and "bot-green:" in compose
    assert "edge_config:/config" in compose
    assert "caddy run --resume" in (root / "deploy" / "edge-entrypoint.sh").read_text(
        encoding="utf-8"
    )
    assert "handle_response @asset_missing" in edge
    assert "lb_retries" not in edge
    assert orchestrator.index('"validate"') < orchestrator.index('"reload"')
    assert "another production deployment owns the host lock" in orchestrator
