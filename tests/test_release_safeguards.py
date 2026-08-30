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
    assert "github.ref == 'refs/heads/dev'" not in ci_workflow
    assert "branches: [master]" in deploy_workflow
    assert "branches: [dev" not in deploy_workflow
    assert "workflow_dispatch:" not in deploy_workflow


def test_auto_release_contract_is_fail_closed_for_medium_and_human_gates() -> None:
    agents, global_rules, lifecycle = _release_policy_sources()

    for source in (agents, global_rules, lifecycle):
        assert "AUTO_RELEASE_ELIGIBLE" in source
        assert "dev ->" in source
        assert "master" in source

    assert "незакрытых `BLOCKER`, `HIGH` и `MEDIUM` ровно ноль" in lifecycle
    assert "owner checkpoint/approve, human evidence или manual visual gate" in lifecycle
    assert "failure/rollback/manual-intervention verdict" in lifecycle
    assert "Direct push в `master` запрещён" in global_rules
    assert "expected PR head SHA" in lifecycle
    assert "required check `checks`" in lifecycle
    assert "fast-forward/sync `dev`" in lifecycle


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
