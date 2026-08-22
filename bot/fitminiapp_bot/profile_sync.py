from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from aiogram import Bot
from aiogram.types import (
    BotCommand,
    BotCommandScopeAllPrivateChats,
    FSInputFile,
    InputProfilePhotoStatic,
)

from .config import settings
from .error_codes import safe_error_code
from .public_profile import (
    AVATAR_PATH,
    EXPECTED_BOT_USERNAME,
    PUBLIC_BOT_DESCRIPTION,
    PUBLIC_BOT_NAME,
    PUBLIC_BOT_SHORT_DESCRIPTION,
    bot_commands,
    canonical_mini_app_url,
    is_valid_public_https_url,
    menu_button,
    menu_button_matches,
)
from .telegram_client import create_bot_api_session

SyncMode = Literal["check", "apply"]
COMMAND_SCOPE = BotCommandScopeAllPrivateChats()

BOTFATHER_FLAGS: dict[str, bool] = {
    "can_join_groups": False,
    "can_read_all_group_messages": False,
    "supports_guest_queries": False,
    "supports_inline_queries": False,
    "can_connect_to_business": False,
    "has_main_web_app": True,
    "has_topics_enabled": False,
    "allows_users_to_create_topics": False,
    "can_manage_bots": False,
}

BOTFATHER_ACTIONS = {
    "can_join_groups": "Отключить Groups в @BotFather.",
    "can_read_all_group_messages": "Включить Group Privacy в @BotFather.",
    "supports_guest_queries": "Отключить Guest Mode в @BotFather.",
    "supports_inline_queries": "Отключить Inline Mode в @BotFather.",
    "can_connect_to_business": "Отключить Secretary/Business mode в @BotFather.",
    "has_topics_enabled": "Отключить Threaded Mode в @BotFather.",
    "allows_users_to_create_topics": "Отключить Threaded Mode в @BotFather.",
    "can_manage_bots": "Отключить Bot Management Mode в @BotFather.",
}


@dataclass(slots=True)
class SyncReport:
    mode: SyncMode
    identity: dict[str, object] = field(default_factory=dict)
    fields: dict[str, dict[str, str]] = field(default_factory=dict)
    botfather_flags: dict[str, dict[str, object]] = field(default_factory=dict)
    owner_actions: list[str] = field(default_factory=list)
    manual_checks: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, object]:
        return {
            "mode": self.mode,
            "identity": self.identity,
            "fields": self.fields,
            "botfather_flags": self.botfather_flags,
            "owner_actions": self.owner_actions,
            "manual_checks": self.manual_checks,
        }

    def exit_code(self) -> int:
        statuses = {value["status"] for value in self.fields.values()}
        if self.identity.get("status") != "VERIFIED" or statuses & {
            "API_ERROR",
            "ASSET_MISSING",
            "VERIFY_FAILED",
        }:
            return 2
        if self.mode == "check":
            has_botfather_mismatch = any(
                value.get("status") == "MISMATCH" for value in self.botfather_flags.values()
            )
            if "DIFF" in statuses or has_botfather_mismatch:
                return 1
        return 0


def _commands_equal(current: list[BotCommand], desired: list[BotCommand]) -> bool:
    return [(item.command, item.description) for item in current] == [
        (item.command, item.description) for item in desired
    ]


def _avatar_file_unique_id(profile_photos: object) -> str | None:
    photos = getattr(profile_photos, "photos", None)
    if not photos or not photos[0]:
        return None
    return photos[0][-1].file_unique_id


def _asset_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_avatar_state(path: Path) -> dict[str, str]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError, json.JSONDecodeError, OSError:
        return {}
    if not isinstance(payload, dict):
        return {}
    return {
        key: value
        for key in ("asset_sha256", "file_unique_id")
        if isinstance((value := payload.get(key)), str)
    }


def _write_avatar_state(path: Path, *, asset_sha256: str, file_unique_id: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    temporary.write_text(
        json.dumps(
            {"asset_sha256": asset_sha256, "file_unique_id": file_unique_id},
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _field(status: str, detail: str) -> dict[str, str]:
    return {"status": status, "detail": detail}


async def _sync_text_field(
    bot: Bot,
    report: SyncReport,
    *,
    field_name: str,
    desired: str,
    getter_name: str,
    setter_name: str,
    response_attribute: str,
) -> None:
    getter = getattr(bot, getter_name)
    setter = getattr(bot, setter_name)
    try:
        current_response = await getter(language_code="")
        current = getattr(current_response, response_attribute)
    except Exception as exc:
        report.fields[field_name] = _field("API_ERROR", safe_error_code(exc))
        return

    if current == desired:
        report.fields[field_name] = _field("MATCH", "remote value already matches")
        return
    if report.mode == "check":
        report.fields[field_name] = _field("DIFF", "remote value differs")
        return

    try:
        await setter(**{field_name: desired}, language_code="")
        verified_response = await getter(language_code="")
        verified = getattr(verified_response, response_attribute)
    except Exception as exc:
        report.fields[field_name] = _field("API_ERROR", safe_error_code(exc))
        return
    report.fields[field_name] = _field(
        "VERIFIED" if verified == desired else "VERIFY_FAILED",
        "updated and read back" if verified == desired else "read-back does not match",
    )


async def _sync_commands(bot: Bot, report: SyncReport) -> None:
    desired = bot_commands()
    try:
        current = await bot.get_my_commands(scope=COMMAND_SCOPE, language_code="")
    except Exception as exc:
        report.fields["commands"] = _field("API_ERROR", safe_error_code(exc))
        return
    if _commands_equal(current, desired):
        report.fields["commands"] = _field("MATCH", "private-chat commands already match")
        return
    if report.mode == "check":
        report.fields["commands"] = _field("DIFF", "private-chat commands differ")
        return
    try:
        await bot.set_my_commands(commands=desired, scope=COMMAND_SCOPE, language_code="")
        verified = await bot.get_my_commands(scope=COMMAND_SCOPE, language_code="")
    except Exception as exc:
        report.fields["commands"] = _field("API_ERROR", safe_error_code(exc))
        return
    matches = _commands_equal(verified, desired)
    report.fields["commands"] = _field(
        "VERIFIED" if matches else "VERIFY_FAILED",
        "updated private scope and read back" if matches else "read-back does not match",
    )


async def _sync_menu_button(bot: Bot, report: SyncReport, frontend_base_url: str) -> None:
    try:
        current = await bot.get_chat_menu_button()
    except Exception as exc:
        report.fields["menu_button"] = _field("API_ERROR", safe_error_code(exc))
        return
    if menu_button_matches(current, frontend_base_url):
        report.fields["menu_button"] = _field("MATCH", "default menu button already matches")
        return
    if report.mode == "check":
        report.fields["menu_button"] = _field("DIFF", "default menu button differs")
        return
    try:
        await bot.set_chat_menu_button(menu_button=menu_button(frontend_base_url))
        verified = await bot.get_chat_menu_button()
    except Exception as exc:
        report.fields["menu_button"] = _field("API_ERROR", safe_error_code(exc))
        return
    matches = menu_button_matches(verified, frontend_base_url)
    report.fields["menu_button"] = _field(
        "VERIFIED" if matches else "VERIFY_FAILED",
        "updated default button and read back" if matches else "read-back does not match",
    )


async def _sync_avatar(
    bot: Bot,
    report: SyncReport,
    *,
    bot_id: int,
    avatar_path: Path,
    avatar_state_path: Path,
) -> None:
    if not avatar_path.is_file():
        report.fields["profile_photo"] = _field("ASSET_MISSING", str(avatar_path))
        return
    asset_hash = _asset_sha256(avatar_path)
    state = _read_avatar_state(avatar_state_path)
    try:
        current = await bot.get_user_profile_photos(user_id=bot_id, limit=1)
        current_file_unique_id = _avatar_file_unique_id(current)
    except Exception as exc:
        report.fields["profile_photo"] = _field("API_ERROR", safe_error_code(exc))
        return

    matches = bool(
        current_file_unique_id
        and state.get("asset_sha256") == asset_hash
        and state.get("file_unique_id") == current_file_unique_id
    )
    if matches:
        report.fields["profile_photo"] = _field("MATCH", "canonical asset identity matches")
        return
    if report.mode == "check":
        detail = (
            "profile photo is absent"
            if current_file_unique_id is None
            else "canonical asset identity is not verified"
        )
        report.fields["profile_photo"] = _field("DIFF", detail)
        return

    try:
        applied = await bot.set_my_profile_photo(
            photo=InputProfilePhotoStatic(
                photo=FSInputFile(avatar_path, filename="yfc-bot-avatar.jpg")
            )
        )
        if applied is not True:
            report.fields["profile_photo"] = _field(
                "VERIFY_FAILED", "Telegram did not confirm the profile photo update"
            )
            return
        verified_photos = await bot.get_user_profile_photos(user_id=bot_id, limit=1)
        verified_file_unique_id = _avatar_file_unique_id(verified_photos)
        if verified_file_unique_id is None or verified_file_unique_id == current_file_unique_id:
            report.fields["profile_photo"] = _field(
                "VERIFY_FAILED", "read-back did not expose the updated profile photo"
            )
            return
        _write_avatar_state(
            avatar_state_path,
            asset_sha256=asset_hash,
            file_unique_id=verified_file_unique_id,
        )
    except Exception as exc:
        report.fields["profile_photo"] = _field("API_ERROR", safe_error_code(exc))
        return
    report.fields["profile_photo"] = _field("VERIFIED", "updated and read back")


def _diagnose_botfather_flags(bot_user: object, report: SyncReport, *, mini_app_url: str) -> None:
    for flag_name, expected in BOTFATHER_FLAGS.items():
        reported = getattr(bot_user, flag_name, None)
        current = False if reported is None else reported
        if current == expected:
            status = "MATCH"
        else:
            status = "MISMATCH"
            action = (
                f"Включить Main Mini App для @your_fitness_coach_bot и указать URL {mini_app_url}"
                if flag_name == "has_main_web_app"
                else BOTFATHER_ACTIONS[flag_name]
            )
            if action not in report.owner_actions:
                report.owner_actions.append(action)
        report.botfather_flags[flag_name] = {
            "status": status,
            "current": current,
            "reported": reported,
            "expected": expected,
        }


async def sync_public_profile(
    bot: Bot,
    *,
    mode: SyncMode,
    frontend_base_url: str,
    avatar_path: Path = AVATAR_PATH,
    avatar_state_path: Path | None = None,
) -> SyncReport:
    report = SyncReport(mode=mode)
    mini_app_url = canonical_mini_app_url(frontend_base_url)
    if not is_valid_public_https_url(mini_app_url):
        report.identity = {"status": "CONFIG_ERROR", "detail": "invalid Mini App HTTPS URL"}
        return report

    try:
        bot_user = await bot.get_me()
    except Exception as exc:
        report.identity = {"status": "API_ERROR", "detail": safe_error_code(exc)}
        return report

    username = getattr(bot_user, "username", None)
    is_bot = getattr(bot_user, "is_bot", False)
    if is_bot is not True or username != EXPECTED_BOT_USERNAME:
        report.identity = {
            "status": "MISMATCH",
            "is_bot": is_bot,
            "username": username,
            "expected_username": EXPECTED_BOT_USERNAME,
        }
        return report

    report.identity = {"status": "VERIFIED", "username": username}
    _diagnose_botfather_flags(bot_user, report, mini_app_url=mini_app_url)
    report.manual_checks.extend(
        [
            "Проверить в @BotFather, что Mini App origin protection не отключена через opt-out.",
            (
                "Проверить, что Main Mini App открывает canonical URL без query-параметров: "
                f"{mini_app_url}"
            ),
        ]
    )

    await _sync_text_field(
        bot,
        report,
        field_name="name",
        desired=PUBLIC_BOT_NAME,
        getter_name="get_my_name",
        setter_name="set_my_name",
        response_attribute="name",
    )
    await _sync_text_field(
        bot,
        report,
        field_name="short_description",
        desired=PUBLIC_BOT_SHORT_DESCRIPTION,
        getter_name="get_my_short_description",
        setter_name="set_my_short_description",
        response_attribute="short_description",
    )
    await _sync_text_field(
        bot,
        report,
        field_name="description",
        desired=PUBLIC_BOT_DESCRIPTION,
        getter_name="get_my_description",
        setter_name="set_my_description",
        response_attribute="description",
    )
    await _sync_commands(bot, report)
    await _sync_menu_button(bot, report, frontend_base_url)
    await _sync_avatar(
        bot,
        report,
        bot_id=bot_user.id,
        avatar_path=avatar_path,
        avatar_state_path=avatar_state_path or Path(settings.bot_profile_sync_state_path),
    )
    return report


async def _run(mode: SyncMode) -> int:
    if not settings.bot_token or settings.bot_token in {"change-me", "replace-me"}:
        report = SyncReport(mode=mode)
        report.identity = {"status": "CONFIG_ERROR", "detail": "bot token is not configured"}
        print(json.dumps(report.as_dict(), ensure_ascii=False, indent=2))
        return report.exit_code()

    session = create_bot_api_session(timeout=15)
    bot = Bot(settings.bot_token, session=session)
    try:
        report = await sync_public_profile(
            bot,
            mode=mode,
            frontend_base_url=settings.frontend_base_url,
        )
    finally:
        await bot.session.close()
    print(json.dumps(report.as_dict(), ensure_ascii=False, indent=2))
    return report.exit_code()


def main() -> None:
    parser = argparse.ArgumentParser(description="Check or apply canonical public Telegram profile")
    parser.add_argument("mode", choices=("check", "apply"))
    args = parser.parse_args()
    raise SystemExit(asyncio.run(_run(args.mode)))


if __name__ == "__main__":
    main()
