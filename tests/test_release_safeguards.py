from pathlib import Path


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

    assert "scripts/zero_downtime_deploy.py" in deploy_script
    assert "docker compose config --quiet" in deploy_script
    assert "--remove-orphans" not in deploy_script
    assert "docker compose up" not in deploy_script


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
