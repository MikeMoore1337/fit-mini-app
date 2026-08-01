import asyncio
from pathlib import Path

import pytest
from aiogram.exceptions import TelegramConflictError
from bot.fitminiapp_bot import bot as bot_module
from bot.fitminiapp_bot.bot import PollingConflict, PollingFileLock, StableDispatcher


class _FakeSession:
    timeout = 10


class _ConflictingBot:
    id = 123
    session = _FakeSession()

    async def __call__(self, method, **kwargs):
        raise TelegramConflictError(method=method, message="terminated by other getUpdates request")


def test_dispatcher_escalates_polling_conflict_without_retrying():
    async def consume_updates() -> None:
        updates = StableDispatcher._listen_updates(_ConflictingBot())

        with pytest.raises(PollingConflict, match="other getUpdates"):
            await anext(updates)

    asyncio.run(consume_updates())


def test_polling_lock_filename_is_stable_and_does_not_expose_token(tmp_path: Path):
    first = PollingFileLock(str(tmp_path), "secret-token")
    second = PollingFileLock(str(tmp_path), "secret-token")

    assert first.path == second.path
    assert "secret-token" not in first.path.name


def test_polling_lock_waiter_takes_over_after_release(tmp_path: Path, monkeypatch):
    if bot_module.fcntl is None:
        pytest.skip("fcntl is only available in the Linux production environment")

    async def exercise_takeover() -> None:
        leader = PollingFileLock(str(tmp_path), "shared-token")
        standby = PollingFileLock(str(tmp_path), "shared-token")
        await leader.acquire()

        async def release_leader(_seconds: float) -> None:
            leader.release()

        monkeypatch.setattr(bot_module.asyncio, "sleep", release_leader)
        try:
            await standby.acquire()
            assert standby._file is not None
        finally:
            leader.release()
            standby.release()

    asyncio.run(exercise_takeover())
