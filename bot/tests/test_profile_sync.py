import asyncio
import hashlib
import json
import logging
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, call

from aiogram.types import BotCommandScopeAllPrivateChats, MenuButtonCommands
from bot.fitminiapp_bot import profile_sync as profile_sync_module
from bot.fitminiapp_bot.profile_sync import SyncReport, sync_public_profile
from bot.fitminiapp_bot.public_profile import (
    AVATAR_PATH,
    EXPECTED_BOT_USERNAME,
    PUBLIC_BOT_DESCRIPTION,
    PUBLIC_BOT_NAME,
    PUBLIC_BOT_SHORT_DESCRIPTION,
    bot_commands,
    menu_button,
)


class FakeBot:
    def __init__(self) -> None:
        self.user = SimpleNamespace(
            id=777,
            is_bot=True,
            username=EXPECTED_BOT_USERNAME,
            can_join_groups=False,
            can_read_all_group_messages=False,
            supports_guest_queries=False,
            supports_inline_queries=False,
            can_connect_to_business=False,
            has_main_web_app=True,
            has_topics_enabled=False,
            allows_users_to_create_topics=False,
            can_manage_bots=False,
        )
        self.name = PUBLIC_BOT_NAME
        self.short_description = PUBLIC_BOT_SHORT_DESCRIPTION
        self.description = PUBLIC_BOT_DESCRIPTION
        self.commands = bot_commands()
        self.menu = menu_button("https://app.your-fitness-coach.ru")
        self.photo_id: str | None = "canonical-photo"
        self.calls: list[tuple[str, object | None]] = []

    async def get_me(self):
        self.calls.append(("get_me", None))
        return self.user

    async def get_my_name(self, *, language_code):
        self.calls.append(("get_my_name", language_code))
        return SimpleNamespace(name=self.name)

    async def set_my_name(self, *, name, language_code):
        self.calls.append(("set_my_name", name))
        self.name = name

    async def get_my_short_description(self, *, language_code):
        self.calls.append(("get_my_short_description", language_code))
        return SimpleNamespace(short_description=self.short_description)

    async def set_my_short_description(self, *, short_description, language_code):
        self.calls.append(("set_my_short_description", short_description))
        self.short_description = short_description

    async def get_my_description(self, *, language_code):
        self.calls.append(("get_my_description", language_code))
        return SimpleNamespace(description=self.description)

    async def set_my_description(self, *, description, language_code):
        self.calls.append(("set_my_description", description))
        self.description = description

    async def get_my_commands(self, *, scope, language_code):
        self.calls.append(("get_my_commands", scope))
        return self.commands

    async def set_my_commands(self, *, commands, scope, language_code):
        self.calls.append(("set_my_commands", scope))
        self.commands = commands

    async def get_chat_menu_button(self):
        self.calls.append(("get_chat_menu_button", None))
        return self.menu

    async def set_chat_menu_button(self, *, menu_button):
        self.calls.append(("set_chat_menu_button", menu_button))
        self.menu = menu_button

    async def get_user_profile_photos(self, *, user_id, limit):
        self.calls.append(("get_user_profile_photos", user_id))
        photos = [] if self.photo_id is None else [[SimpleNamespace(file_unique_id=self.photo_id)]]
        return SimpleNamespace(photos=photos)

    async def set_my_profile_photo(self, *, photo):
        self.calls.append(("set_my_profile_photo", photo))
        self.photo_id = "canonical-photo"
        return True


def write_avatar_state(path: Path, file_unique_id: str = "canonical-photo") -> None:
    path.write_text(
        json.dumps(
            {
                "asset_sha256": hashlib.sha256(AVATAR_PATH.read_bytes()).hexdigest(),
                "file_unique_id": file_unique_id,
            }
        ),
        encoding="utf-8",
    )


def setter_calls(bot: FakeBot) -> list[str]:
    return [name for name, _ in bot.calls if name.startswith("set_")]


def test_public_profile_values_fit_telegram_limits() -> None:
    assert len(PUBLIC_BOT_NAME) <= 64
    assert len(PUBLIC_BOT_SHORT_DESCRIPTION) <= 120
    assert len(PUBLIC_BOT_DESCRIPTION) <= 512
    assert AVATAR_PATH.suffix == ".jpg"
    assert AVATAR_PATH.read_bytes().startswith(b"\xff\xd8\xff")
    for command in bot_commands():
        assert 1 <= len(command.command) <= 32
        assert 1 <= len(command.description) <= 256


def test_wrong_username_guard_stops_before_reads_and_writes(tmp_path: Path) -> None:
    bot = FakeBot()
    bot.user.username = "another_bot"

    report = asyncio.run(
        sync_public_profile(
            bot,
            mode="apply",
            frontend_base_url="https://app.your-fitness-coach.ru",
            avatar_state_path=tmp_path / "state.json",
        )
    )

    assert report.identity["status"] == "MISMATCH"
    assert bot.calls == [("get_me", None)]
    assert report.fields == {}


def test_check_reports_diff_without_writes_and_uses_private_command_scope(tmp_path: Path) -> None:
    bot = FakeBot()
    bot.name = "Old name"
    bot.commands = []
    bot.menu = MenuButtonCommands()
    bot.photo_id = None

    report = asyncio.run(
        sync_public_profile(
            bot,
            mode="check",
            frontend_base_url="https://app.your-fitness-coach.ru",
            avatar_state_path=tmp_path / "state.json",
        )
    )

    assert report.fields["name"]["status"] == "DIFF"
    assert report.fields["commands"]["status"] == "DIFF"
    assert report.fields["menu_button"]["status"] == "DIFF"
    assert report.fields["profile_photo"]["status"] == "DIFF"
    assert setter_calls(bot) == []
    command_scope = next(value for name, value in bot.calls if name == "get_my_commands")
    assert isinstance(command_scope, BotCommandScopeAllPrivateChats)


def test_invalid_base_url_stops_before_identity_check_and_writes(tmp_path: Path) -> None:
    bot = FakeBot()

    report = asyncio.run(
        sync_public_profile(
            bot,
            mode="apply",
            frontend_base_url="https://app.your-fitness-coach.ru?preview=1",
            avatar_state_path=tmp_path / "state.json",
        )
    )

    assert report.identity["status"] == "CONFIG_ERROR"
    assert bot.calls == []


def test_noop_apply_does_not_write_remote_state(tmp_path: Path) -> None:
    state_path = tmp_path / "state.json"
    write_avatar_state(state_path)
    bot = FakeBot()

    report = asyncio.run(
        sync_public_profile(
            bot,
            mode="apply",
            frontend_base_url="https://app.your-fitness-coach.ru",
            avatar_state_path=state_path,
        )
    )

    assert all(field["status"] == "MATCH" for field in report.fields.values())
    assert setter_calls(bot) == []


def test_partial_diff_changes_only_name_and_verifies_readback(tmp_path: Path) -> None:
    state_path = tmp_path / "state.json"
    write_avatar_state(state_path)
    bot = FakeBot()
    bot.name = "Outdated"

    report = asyncio.run(
        sync_public_profile(
            bot,
            mode="apply",
            frontend_base_url="https://app.your-fitness-coach.ru",
            avatar_state_path=state_path,
        )
    )

    assert report.fields["name"]["status"] == "VERIFIED"
    assert setter_calls(bot) == ["set_my_name"]


def test_avatar_apply_records_readback_identity_and_second_apply_is_noop(tmp_path: Path) -> None:
    state_path = tmp_path / "state.json"
    bot = FakeBot()
    bot.photo_id = "legacy-photo"

    first = asyncio.run(
        sync_public_profile(
            bot,
            mode="apply",
            frontend_base_url="https://app.your-fitness-coach.ru",
            avatar_state_path=state_path,
        )
    )
    assert first.fields["profile_photo"]["status"] == "VERIFIED"
    assert setter_calls(bot) == ["set_my_profile_photo"]
    assert json.loads(state_path.read_text(encoding="utf-8"))["file_unique_id"] == "canonical-photo"

    bot.calls.clear()
    second = asyncio.run(
        sync_public_profile(
            bot,
            mode="apply",
            frontend_base_url="https://app.your-fitness-coach.ru",
            avatar_state_path=state_path,
        )
    )
    assert second.fields["profile_photo"]["status"] == "MATCH"
    assert setter_calls(bot) == []


def test_avatar_apply_rejects_stale_readback(tmp_path: Path) -> None:
    state_path = tmp_path / "state.json"
    bot = FakeBot()
    bot.photo_id = "legacy-photo"

    async def accept_without_visible_change(*, photo):
        bot.calls.append(("set_my_profile_photo", photo))
        return True

    bot.set_my_profile_photo = accept_without_visible_change
    report = asyncio.run(
        sync_public_profile(
            bot,
            mode="apply",
            frontend_base_url="https://app.your-fitness-coach.ru",
            avatar_state_path=state_path,
        )
    )

    assert report.fields["profile_photo"]["status"] == "VERIFY_FAILED"
    assert not state_path.exists()


def test_api_failure_is_bounded_and_does_not_log_secret(tmp_path: Path, caplog) -> None:
    state_path = tmp_path / "state.json"
    write_avatar_state(state_path)
    bot = FakeBot()

    async def fail_name(*, language_code):
        raise RuntimeError("request used 123456:super-secret-token")

    bot.get_my_name = fail_name
    with caplog.at_level(logging.DEBUG):
        report = asyncio.run(
            sync_public_profile(
                bot,
                mode="apply",
                frontend_base_url="https://app.your-fitness-coach.ru",
                avatar_state_path=state_path,
            )
        )

    assert report.fields["name"]["status"] == "API_ERROR"
    assert "super-secret-token" not in json.dumps(report.as_dict())
    assert "super-secret-token" not in caplog.text
    assert setter_calls(bot) == []


def test_botfather_report_contains_only_actual_mismatch_actions(tmp_path: Path) -> None:
    state_path = tmp_path / "state.json"
    write_avatar_state(state_path)
    bot = FakeBot()
    bot.user.can_join_groups = True
    bot.user.supports_inline_queries = True

    report = asyncio.run(
        sync_public_profile(
            bot,
            mode="check",
            frontend_base_url="https://app.your-fitness-coach.ru",
            avatar_state_path=state_path,
        )
    )

    assert report.botfather_flags["can_join_groups"]["status"] == "MISMATCH"
    assert report.botfather_flags["supports_inline_queries"]["status"] == "MISMATCH"
    assert len(report.owner_actions) == 2
    assert all("name" not in action.lower() for action in report.owner_actions)
    assert report.exit_code() == 1


def test_absent_optional_flags_are_false_and_missing_main_app_is_a_mismatch(tmp_path: Path) -> None:
    state_path = tmp_path / "state.json"
    write_avatar_state(state_path)
    bot = FakeBot()
    bot.user.supports_inline_queries = None
    bot.user.has_main_web_app = None

    report = asyncio.run(
        sync_public_profile(
            bot,
            mode="check",
            frontend_base_url="https://app.your-fitness-coach.ru",
            avatar_state_path=state_path,
        )
    )

    assert report.botfather_flags["supports_inline_queries"]["status"] == "MATCH"
    assert report.botfather_flags["supports_inline_queries"]["current"] is False
    assert report.botfather_flags["has_main_web_app"]["status"] == "MISMATCH"
    assert report.botfather_flags["has_main_web_app"]["current"] is False
    assert report.exit_code() == 1
    assert any("https://app.your-fitness-coach.ru/app" in action for action in report.owner_actions)


def test_profile_sync_retries_transient_api_error_and_recovers(monkeypatch) -> None:
    api_error = SyncReport(mode="apply", identity={"status": "API_ERROR"})
    matched = SyncReport(mode="apply", identity={"status": "VERIFIED"})
    sync = AsyncMock(side_effect=[api_error, matched])
    sleep = AsyncMock()
    monkeypatch.setattr(profile_sync_module, "sync_public_profile", sync)
    monkeypatch.setattr(profile_sync_module.asyncio, "sleep", sleep)

    report = asyncio.run(
        profile_sync_module._sync_public_profile_with_retry(
            object(),
            mode="apply",
            frontend_base_url="https://app.your-fitness-coach.ru",
        )
    )

    assert report is matched
    assert sync.await_count == 2
    sleep.assert_awaited_once_with(1)


def test_profile_sync_retry_is_bounded(monkeypatch) -> None:
    api_error = SyncReport(
        mode="check",
        identity={"status": "VERIFIED"},
        fields={"commands": {"status": "API_ERROR", "detail": "transport_error"}},
    )
    sync = AsyncMock(return_value=api_error)
    sleep = AsyncMock()
    monkeypatch.setattr(profile_sync_module, "sync_public_profile", sync)
    monkeypatch.setattr(profile_sync_module.asyncio, "sleep", sleep)

    report = asyncio.run(
        profile_sync_module._sync_public_profile_with_retry(
            object(),
            mode="check",
            frontend_base_url="https://app.your-fitness-coach.ru",
        )
    )

    assert report is api_error
    assert sync.await_count == 3
    assert sleep.await_args_list == [call(1), call(2)]
