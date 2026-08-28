from __future__ import annotations

import subprocess
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace

import pytest
from scripts import zero_downtime_deploy as deploy

OLD_SHA = "a" * 40
NEW_SHA = "b" * 40


class FakeProbe:
    def poll(self):
        return None


def _config(tmp_path: Path) -> deploy.DeployConfig:
    return deploy.DeployConfig(
        target_revision=NEW_SHA,
        base_url="https://app.example.test",
        public_base_url="https://example.test",
        backend_image=f"registry/backend:{NEW_SHA}",
        bot_image=f"registry/bot:{NEW_SHA}",
        root=tmp_path,
        state_root=tmp_path / ".artifacts" / "deployments",
        observation_seconds=1,
        readiness_timeout_seconds=5,
        probe_interval_seconds=0.1,
        probe_timeout_seconds=1,
        backend_drain_seconds=45,
        worker_drain_seconds=120,
        bot_drain_seconds=60,
        bot_polling_enabled=True,
    )


def _state(config: deploy.DeployConfig, *, revision: str = OLD_SHA) -> None:
    state = deploy.ReleaseState(
        version=1,
        active_slot="blue",
        active_revision=revision,
        active_backend_image="registry/backend@sha256:" + "1" * 64,
        active_bot_image="registry/bot@sha256:" + "2" * 64,
    )
    deploy._atomic_json(config.state_root / "state.json", asdict(state))


def _patch_runtime(monkeypatch, *, fail_at: str | None = None):
    calls: dict[str, list] = {
        "compose": [],
        "switch": [],
        "run": [],
        "consumer_start": [],
        "consumer_stop": [],
    }

    def compose(*args, **kwargs):
        del kwargs
        calls["compose"].append(args)
        if fail_at == "candidate_start" and "backend-green" in args and "up" in args:
            raise subprocess.CalledProcessError(1, args)
        return subprocess.CompletedProcess(args, 0, stdout="backend-green\n", stderr="")

    public_smoke_count = 0

    def public_smoke(_config):
        nonlocal public_smoke_count
        public_smoke_count += 1
        if fail_at == "external_smoke" and public_smoke_count == 2:
            raise deploy.DeploymentError("external smoke failed")

    def run(args, **kwargs):
        del kwargs
        calls["run"].append(args)
        if fail_at == "migration" and "scripts/check_online_migrations.py" in args:
            raise subprocess.CalledProcessError(1, args)
        return subprocess.CompletedProcess(args, 0, stdout="", stderr="")

    def switch(active, fallback):
        calls["switch"].append((active, fallback))
        if fail_at == "gateway" and active == "green":
            raise deploy.DeploymentError("invalid gateway config")

    def candidate_smoke(slot):
        if fail_at == "candidate_smoke":
            raise deploy.DeploymentError(f"{slot} smoke failed")

    def start_consumers(slot, **kwargs):
        del kwargs
        calls["consumer_start"].append(slot)
        if fail_at == "consumer" and slot == "green":
            raise deploy.DeploymentError("consumer ownership failed")

    def stop_consumers(slot, config, **kwargs):
        del kwargs
        assert config.worker_drain_seconds == 120
        calls["consumer_stop"].append(slot)

    monkeypatch.setattr(deploy, "_capacity", lambda: {"cpu_count": 4})
    monkeypatch.setattr(deploy, "_compose", compose)
    monkeypatch.setattr(deploy, "_run", run)
    monkeypatch.setattr(deploy, "_public_smoke", public_smoke)
    monkeypatch.setattr(deploy, "_switch_gateway", switch)
    monkeypatch.setattr(deploy, "_candidate_smoke", candidate_smoke)
    monkeypatch.setattr(
        deploy, "_image_digest", lambda image, revision: image + "@sha256:" + "3" * 64
    )
    monkeypatch.setattr(deploy, "_start_probe", lambda *args: FakeProbe())
    monkeypatch.setattr(deploy, "_finish_probe", lambda *args: {"failure_count": 0})

    def wait_observation(*args):
        del args
        if fail_at == "interrupt":
            raise KeyboardInterrupt

    monkeypatch.setattr(deploy, "_wait_observation", wait_observation)
    monkeypatch.setattr(deploy, "_stop_slot_consumers", stop_consumers)
    monkeypatch.setattr(deploy, "_start_slot_consumers", start_consumers)
    return calls


def test_successful_rollout_updates_state_only_after_observation(
    tmp_path: Path, monkeypatch
) -> None:
    config = _config(tmp_path)
    _state(config)
    calls = _patch_runtime(monkeypatch)

    evidence = deploy.deploy(config)

    state = deploy.ReleaseState.from_path(config.state_root / "state.json")
    assert evidence.verdict == "active"
    assert state.active_slot == "green"
    assert state.active_revision == NEW_SHA
    assert state.rollback_revision == OLD_SHA
    assert calls["switch"] == [("blue", "blue"), ("green", "blue"), ("green", "green")]


@pytest.mark.parametrize("fail_at", ["candidate_start", "candidate_smoke", "gateway", "migration"])
def test_pre_switch_failure_preserves_active_state(
    tmp_path: Path, monkeypatch, fail_at: str
) -> None:
    config = _config(tmp_path)
    _state(config)
    calls = _patch_runtime(monkeypatch, fail_at=fail_at)

    with pytest.raises((deploy.DeploymentError, subprocess.CalledProcessError)):
        deploy.deploy(config)

    state = deploy.ReleaseState.from_path(config.state_root / "state.json")
    assert state.active_revision == OLD_SHA
    assert ("green", "blue") not in calls["switch"] or fail_at == "gateway"


def test_post_switch_failure_reloads_verified_old_route(tmp_path: Path, monkeypatch) -> None:
    config = _config(tmp_path)
    _state(config)
    calls = _patch_runtime(monkeypatch, fail_at="external_smoke")

    with pytest.raises(deploy.DeploymentError, match="external smoke"):
        deploy.deploy(config)

    assert calls["switch"][-1] == ("blue", "blue")
    assert (
        deploy.ReleaseState.from_path(config.state_root / "state.json").active_revision == OLD_SHA
    )


def test_partial_consumer_handoff_restores_the_previous_single_owner(
    tmp_path: Path, monkeypatch
) -> None:
    config = _config(tmp_path)
    _state(config)
    calls = _patch_runtime(monkeypatch, fail_at="consumer")

    with pytest.raises(deploy.DeploymentError, match="consumer ownership"):
        deploy.deploy(config)

    assert calls["switch"][-1] == ("blue", "blue")
    assert calls["consumer_stop"] == ["blue", "green"]
    assert calls["consumer_start"] == ["green", "blue"]


def test_interrupted_post_switch_rollout_restores_state_and_route(
    tmp_path: Path, monkeypatch
) -> None:
    config = _config(tmp_path)
    _state(config)
    calls = _patch_runtime(monkeypatch, fail_at="interrupt")

    with pytest.raises(KeyboardInterrupt):
        deploy.deploy(config)

    assert calls["switch"][-1] == ("blue", "blue")
    assert (
        deploy.ReleaseState.from_path(config.state_root / "state.json").active_revision == OLD_SHA
    )


def test_repeated_same_sha_is_a_verified_no_op(tmp_path: Path, monkeypatch) -> None:
    config = _config(tmp_path)
    _state(config, revision=NEW_SHA)
    calls = _patch_runtime(monkeypatch)
    smoke = []
    monkeypatch.setattr(deploy, "_public_smoke", lambda value: smoke.append(value.base_url))

    evidence = deploy.deploy(config)

    assert evidence.verdict == "active"
    assert smoke == [config.base_url]
    assert calls["switch"] == [("blue", "blue")]


def test_gateway_switch_validates_before_atomic_reload(monkeypatch) -> None:
    commands = []
    reloaded = False

    def compose(*args, **kwargs):
        nonlocal reloaded
        commands.append(args)
        if "reload" in args:
            reloaded = True
        if "adapt" in args:
            output = '{"apps":{"dial":"backend-green:8000"}}'
        elif any("reverse_proxy/upstreams" in part for part in args):
            output = '[{"num_requests":0}]'
        elif any("2019/config/" in part for part in args):
            dial = "backend-green:8000" if reloaded else "backend-blue:8000"
            output = f'{{"apps":{{"dial":"{dial}"}}}}'
        else:
            output = ""
        return subprocess.CompletedProcess(args, 0, stdout=output, stderr="")

    monkeypatch.setattr(deploy, "_compose", compose)

    deploy._switch_gateway("green", "blue")

    assert "validate" in commands[0]
    assert any("reload" in command for command in commands)
    assert commands.index(
        next(command for command in commands if "validate" in command)
    ) < commands.index(next(command for command in commands if "reload" in command))
    assert any("YFC_ASSET_FALLBACK_UPSTREAM=backend-blue:8000" in part for part in commands[0])


def test_current_run_logs_use_the_container_start_boundary(monkeypatch) -> None:
    commands = []

    def compose(*args, **kwargs):
        del kwargs
        commands.append(args)
        return subprocess.CompletedProcess(args, 0, stdout="current run\n", stderr="")

    monkeypatch.setattr(deploy, "_compose", compose)
    lease = deploy.ConsumerLease(
        service="bot-green",
        container_id="container-new",
        started_at="2026-08-28T12:00:00.000000000Z",
        required_markers=("polling_file_lock_acquired", "telegram_polling_started"),
    )

    assert deploy._current_run_logs(lease) == "current run\n"
    assert commands == [
        (
            "logs",
            "--no-color",
            "--since",
            "2026-08-28T12:00:00.000000000Z",
            "bot-green",
        )
    ]


def test_bot_lease_requires_lock_and_polling_markers_from_current_run(monkeypatch) -> None:
    lease = deploy.ConsumerLease(
        service="bot-green",
        container_id="container-new",
        started_at="2026-08-28T12:00:00Z",
        required_markers=("polling_file_lock_acquired", "telegram_polling_started"),
    )
    monkeypatch.setattr(deploy, "_service_is_running", lambda service: service == "bot-green")
    monkeypatch.setattr(
        deploy,
        "_compose",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args, 0, stdout="container-new\n", stderr=""
        ),
    )
    monkeypatch.setattr(
        deploy,
        "_run",
        lambda args, **kwargs: subprocess.CompletedProcess(
            args,
            0,
            stdout=("2026-08-28T12:00:00Z\n" if "{{.State.StartedAt}}" in args else "running\n"),
            stderr="",
        ),
    )
    monkeypatch.setattr(deploy, "_current_run_logs", lambda value: "telegram_polling_started\n")

    assert deploy._lease_is_current_and_healthy(lease) is False


def test_consumer_lease_rejects_restart_with_same_container_id(monkeypatch) -> None:
    lease = deploy.ConsumerLease(
        service="worker-green",
        container_id="container-same",
        started_at="2026-08-28T12:00:00Z",
        required_markers=("worker_started",),
    )
    monkeypatch.setattr(deploy, "_service_is_running", lambda service: True)
    monkeypatch.setattr(
        deploy,
        "_compose",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args, 0, stdout="container-same\n", stderr=""
        ),
    )
    monkeypatch.setattr(
        deploy,
        "_run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args, 0, stdout="2026-08-28T12:05:00Z\n", stderr=""
        ),
    )
    monkeypatch.setattr(
        deploy,
        "_current_run_logs",
        lambda value: "worker_started\nworker_stopped\nworker_started\n",
    )

    assert deploy._lease_is_current_and_healthy(lease) is False


def test_config_reads_drain_and_polling_values_from_compose_dotenv(
    tmp_path: Path, monkeypatch
) -> None:
    (tmp_path / ".env").write_text(
        "DEPLOY_WORKER_DRAIN_SECONDS=300s\nBOT_POLLING_ENABLED=false\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("BACKEND_IMAGE", "registry/backend:" + NEW_SHA)
    monkeypatch.setenv("BOT_IMAGE", "registry/bot:" + NEW_SHA)
    monkeypatch.delenv("DEPLOY_WORKER_DRAIN_SECONDS", raising=False)
    monkeypatch.delenv("BOT_POLLING_ENABLED", raising=False)

    config = deploy._config(
        SimpleNamespace(
            target_revision=NEW_SHA,
            base_url="https://app.example.test",
            public_base_url="https://example.test",
        )
    )

    assert config.worker_drain_seconds == 300
    assert config.bot_polling_enabled is False


def test_consumer_stop_uses_configured_drain_and_requires_worker_ack(
    tmp_path: Path, monkeypatch
) -> None:
    config = _config(tmp_path)
    commands = []
    lease = deploy.ConsumerLease(
        service="worker-blue",
        container_id="worker-current",
        started_at="2026-08-28T12:00:00Z",
        required_markers=("worker_started",),
    )
    monkeypatch.setattr(deploy, "_consumer_lease", lambda *args: lease)
    monkeypatch.setattr(deploy, "_service_is_running", lambda service: True)
    monkeypatch.setattr(deploy, "_current_run_logs", lambda value: "worker_stopped\n")
    monkeypatch.setattr(
        deploy,
        "_compose",
        lambda *args, **kwargs: (
            commands.append(args) or subprocess.CompletedProcess(args, 0, stdout="", stderr="")
        ),
    )

    deploy._stop_slot_consumers("blue", config)

    assert commands == [
        ("stop", "-t", "120", "worker-blue"),
        ("stop", "-t", "60", "bot-blue"),
    ]


def test_consumer_stop_fails_closed_when_worker_drain_is_unconfirmed(
    tmp_path: Path, monkeypatch
) -> None:
    config = _config(tmp_path)
    commands = []
    lease = deploy.ConsumerLease(
        service="worker-blue",
        container_id="worker-current",
        started_at="2026-08-28T12:00:00Z",
        required_markers=("worker_started",),
    )
    monkeypatch.setattr(deploy, "_consumer_lease", lambda *args: lease)
    monkeypatch.setattr(deploy, "_service_is_running", lambda service: True)
    monkeypatch.setattr(deploy, "_current_run_logs", lambda value: "worker_drain_requested\n")
    monkeypatch.setattr(
        deploy,
        "_compose",
        lambda *args, **kwargs: (
            commands.append(args) or subprocess.CompletedProcess(args, 0, stdout="", stderr="")
        ),
    )

    with pytest.raises(deploy.DeploymentError, match="consumer state is uncertain"):
        deploy._stop_slot_consumers("blue", config)

    assert commands == [("stop", "-t", "120", "worker-blue")]


def test_manual_rollback_swaps_only_verified_revisions(tmp_path: Path, monkeypatch) -> None:
    config = _config(tmp_path)
    state = deploy.ReleaseState(
        version=1,
        active_slot="green",
        active_revision=NEW_SHA,
        active_backend_image="registry/backend@sha256:" + "3" * 64,
        active_bot_image="registry/bot@sha256:" + "4" * 64,
        rollback_slot="blue",
        rollback_revision=OLD_SHA,
        rollback_backend_image="registry/backend@sha256:" + "1" * 64,
        rollback_bot_image="registry/bot@sha256:" + "2" * 64,
    )
    deploy._atomic_json(config.state_root / "state.json", asdict(state))
    calls = _patch_runtime(monkeypatch)

    deploy.rollback(config)

    restored = deploy.ReleaseState.from_path(config.state_root / "state.json")
    assert restored.active_revision == OLD_SHA
    assert restored.rollback_revision == NEW_SHA
    assert calls["switch"] == [("blue", "green")]
