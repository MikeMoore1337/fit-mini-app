from pathlib import Path


def test_automated_deploy_keeps_revision_provenance_and_stale_run_guards() -> None:
    root = Path(__file__).resolve().parents[1]
    ci_workflow = (root / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    deploy_workflow = (root / ".github" / "workflows" / "deploy.yml").read_text(encoding="utf-8")
    deploy_script = (root / "scripts" / "deploy_production.sh").read_text(encoding="utf-8")

    assert "org.opencontainers.image.revision=${{ github.sha }}" in ci_workflow
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

    assert 'verify_image_revision "$BACKEND_IMAGE"' in deploy_script
    assert 'verify_image_revision "$BOT_IMAGE"' in deploy_script
    assert deploy_script.index('verify_image_revision "$BOT_IMAGE"') < deploy_script.index(
        "Creating a pre-deploy database backup"
    )
    assert 'scripts/check_deployment.py "$BASE_URL" --expected-environment prod' in deploy_script
    assert deploy_script.index("--expected-environment prod") < deploy_script.index(
        "last-successful-revision"
    )
