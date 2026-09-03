from __future__ import annotations

import json
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[3]
WORKER_ROOT = WORKSPACE / "deploy" / "hermes-editorial-worker"


def test_dockerfile_keeps_the_hardened_runtime_boundary() -> None:
    dockerfile = (WORKER_ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert (
        "FROM python:3.13-alpine@sha256:46ee549c88617e9bc8acb843a326f1a5c0fa5608d7f9703509efe6d53b55f318"
        in dockerfile
    )
    assert (
        "# syntax=docker/dockerfile:1@sha256:ecfaec9ed6d810b56388c508f4121597bfbba70d41a6dfeee4d8cad5f295fc32"
        in dockerfile
    )
    assert "--require-hashes" in dockerfile
    assert "ARG UPSTREAM_" not in dockerfile
    assert "HERMES_RUNTIME_UPSTREAM_TAG=v2026.8.31" in dockerfile
    assert "HERMES_RUNTIME_UPSTREAM_COMMIT=29112bef099274229cadff79cdff7bf7b99c4b77" in dockerfile
    assert "USER 10000:10000" in dockerfile
    assert 'VOLUME ["/opt/data"]' in dockerfile
    assert 'ENTRYPOINT ["python", "/opt/hermes/editorial_worker.py"]' in dockerfile
    assert "--cap-drop" not in dockerfile
    assert "EXPOSE" not in dockerfile
    assert "docker.sock" not in dockerfile
    assert "ffmpeg" not in dockerfile.casefold()
    assert "chromium" not in dockerfile.casefold()
    assert "/bin/busybox" in dockerfile


def test_license_bundle_has_a_deterministic_notice_generator() -> None:
    bundle = (WORKER_ROOT / "license_bundle.py").read_text(encoding="utf-8")
    assert 'output / "NOTICE"' in bundle
    assert 'newline="\\n"' in bundle


def test_provenance_and_dependency_inventory_are_exact() -> None:
    provenance = json.loads((WORKER_ROOT / "hermes-provenance.json").read_text(encoding="utf-8"))
    inventory = json.loads(
        (WORKER_ROOT / "LICENSES" / "package-license-inventory.json").read_text(encoding="utf-8")
    )
    assert provenance["upstream"]["version"] == "0.21.0"
    assert (
        provenance["upstream"]["repository"] == "https://github.com/NousResearch/hermes-agent.git"
    )
    assert provenance["upstream"]["tag"] == "v2026.8.31"
    assert provenance["upstream"]["commit"] == "29112bef099274229cadff79cdff7bf7b99c4b77"
    assert provenance["worker"]["sourceBehaviorPatches"] == 0
    assert provenance["worker"]["publishCapability"] is False
    assert provenance["worker"]["telegramCapability"] is False
    assert provenance["worker"]["toolCapability"] is False
    assert all(item["version"] for item in inventory["pythonPackages"])
    assert len(inventory["pythonPackages"]) == 12


def test_worker_source_has_no_runtime_tool_or_publish_imports() -> None:
    source = (WORKER_ROOT / "editorial_worker.py").read_text(encoding="utf-8").casefold()
    assert "import subprocess" not in source
    assert "docker.sock" not in source
    assert "sendmessage" not in source
    assert "sendphoto" not in source
    assert "publish_endpoint" not in source
