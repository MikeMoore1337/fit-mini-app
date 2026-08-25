import hmac
from typing import Annotated, cast

from fastapi import APIRouter, Header, HTTPException, Path
from sqlalchemy.orm import Session

from fitminiapp_api.core.config import settings
from fitminiapp_api.core.timezone import is_valid_timezone
from fitminiapp_api.db.session import get_session_context
from fitminiapp_api.models.notification import NotificationSetting
from fitminiapp_api.models.user import User, UserProfile
from fitminiapp_api.schemas.bot import (
    BotNewsModerationRequest,
    BotNewsModerationResponse,
    BotSupportCaseCreateRequest,
    BotSupportCaseCreateResponse,
    BotSupportCaseStatus,
    BotSupportRelayResultRequest,
    BotSupportReplyClaimRequest,
    BotSupportReplyClaimResponse,
    BotSupportReplyResultRequest,
    BotSupportReplyResultResponse,
    BotTelegramLinkRequest,
    BotTelegramLinkResponse,
    BotTimezoneUpdateRequest,
    BotTimezoneUpdateResponse,
)
from fitminiapp_api.services.account_linking import (
    TelegramLinkConflictError,
    TelegramLinkError,
    link_telegram_account,
)
from fitminiapp_api.services.bot_support import (
    SupportRateLimitError,
    claim_support_reply,
    complete_support_reply,
    create_support_case,
    record_support_relay_result,
)
from fitminiapp_api.services.news_editorial import moderate_draft
from fitminiapp_api.services.password_auth import PasswordAuthError
from fitminiapp_api.services.telegram_auth import (
    get_or_insert_telegram_user,
    normalize_telegram_username,
)

router = APIRouter()
SupportCaseId = Annotated[str, Path(pattern=r"^[0-9a-f]{32}$")]
NewsDraftId = Annotated[str, Path(pattern=r"^[0-9a-f]{32}$")]


def _check_bot_token(x_bot_token: str | None) -> None:
    expected = settings.bot_internal_token
    if not expected:
        raise HTTPException(status_code=503, detail="Bot internal token is not configured")
    if not x_bot_token or not hmac.compare_digest(x_bot_token, expected):
        raise HTTPException(status_code=403, detail="Forbidden")


def _check_support_admin(telegram_user_id: int) -> None:
    if telegram_user_id not in settings.admin_telegram_id_set:
        raise HTTPException(status_code=403, detail="Forbidden")


def _get_or_create_user(db: Session, payload: BotTimezoneUpdateRequest) -> User:
    username = normalize_telegram_username(payload.username)
    user = get_or_insert_telegram_user(
        db,
        telegram_user_id=payload.telegram_user_id,
        username=username,
        first_name=payload.first_name,
        last_name=payload.last_name,
        photo_url=None,
    )
    user = db.query(User).filter(User.id == user.id).with_for_update().one()
    if payload.username is not None:
        user.username = username
    if payload.first_name is not None:
        user.first_name = payload.first_name
    if payload.last_name is not None:
        user.last_name = payload.last_name

    return user


def _ensure_profile_and_settings(db: Session, user: User) -> UserProfile:
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    if not profile:
        full_name = (
            " ".join(part for part in [user.first_name, user.last_name] if part).strip()
            or user.username
            or f"User {user.telegram_user_id}"
        )
        profile = UserProfile(user_id=user.id, full_name=full_name)
        db.add(profile)
        db.flush()

    setting = db.query(NotificationSetting).filter(NotificationSetting.user_id == user.id).first()
    if not setting:
        db.add(NotificationSetting(user_id=user.id))

    return profile


@router.post("/timezone", response_model=BotTimezoneUpdateResponse)
def update_timezone_from_bot(
    payload: BotTimezoneUpdateRequest,
    x_bot_token: str | None = Header(default=None),
):
    _check_bot_token(x_bot_token)
    if not is_valid_timezone(payload.timezone):
        raise HTTPException(status_code=400, detail="Unsupported timezone")

    with get_session_context() as db:
        user = _get_or_create_user(db, payload)
        profile = _ensure_profile_and_settings(db, user)
        profile.timezone = payload.timezone
        db.flush()

        return BotTimezoneUpdateResponse(
            telegram_user_id=payload.telegram_user_id,
            timezone=profile.timezone,
        )


@router.post("/link-telegram", response_model=BotTelegramLinkResponse)
def link_telegram_from_bot(
    payload: BotTelegramLinkRequest,
    x_bot_token: str | None = Header(default=None),
) -> BotTelegramLinkResponse:
    _check_bot_token(x_bot_token)
    conflict: TelegramLinkConflictError | None = None
    try:
        with get_session_context() as db:
            try:
                result = link_telegram_account(
                    db,
                    raw_token=payload.token,
                    telegram_user_id=payload.telegram_user_id,
                    username=payload.username,
                    first_name=payload.first_name,
                    last_name=payload.last_name,
                )
            except TelegramLinkConflictError as exc:
                # The token stays consumed even on a conflict, so a leaked link
                # cannot be tried against another Telegram account.
                conflict = exc
                result = None
        if conflict is not None:
            raise HTTPException(status_code=409, detail=str(conflict))
        assert result is not None
        return BotTelegramLinkResponse(status=result.status)
    except PasswordAuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except TelegramLinkError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/support/cases", response_model=BotSupportCaseCreateResponse)
def create_support_case_from_bot(
    payload: BotSupportCaseCreateRequest,
    x_bot_token: str | None = Header(default=None),
) -> BotSupportCaseCreateResponse:
    _check_bot_token(x_bot_token)
    try:
        with get_session_context() as db:
            result = create_support_case(
                db,
                telegram_user_id=payload.telegram_user_id,
                request_message_id=payload.request_message_id,
                category=payload.category,
            )
            return BotSupportCaseCreateResponse(
                case_id=result.case.id,
                status="created" if result.created else "duplicate",
                case_status=cast(BotSupportCaseStatus, result.case.status),
            )
    except SupportRateLimitError as exc:
        raise HTTPException(status_code=429, detail="Too many support requests") from exc


@router.post("/support/cases/{case_id}/relay-result")
def update_support_relay_result_from_bot(
    case_id: SupportCaseId,
    payload: BotSupportRelayResultRequest,
    x_bot_token: str | None = Header(default=None),
) -> dict[str, str]:
    _check_bot_token(x_bot_token)
    with get_session_context() as db:
        case = record_support_relay_result(db, case_id=case_id, delivered=payload.delivered)
        if case is None:
            raise HTTPException(status_code=404, detail="Support case not found")
        return {"status": case.status}


@router.post(
    "/support/cases/{case_id}/reply-claim",
    response_model=BotSupportReplyClaimResponse,
)
def claim_support_reply_from_bot(
    case_id: SupportCaseId,
    payload: BotSupportReplyClaimRequest,
    x_bot_token: str | None = Header(default=None),
) -> BotSupportReplyClaimResponse:
    _check_bot_token(x_bot_token)
    _check_support_admin(payload.admin_telegram_user_id)
    with get_session_context() as db:
        claim = claim_support_reply(
            db,
            case_id=case_id,
            admin_telegram_user_id=payload.admin_telegram_user_id,
            reply_message_id=payload.reply_message_id,
        )
        return BotSupportReplyClaimResponse(
            status=claim.status,
            telegram_user_id=claim.telegram_user_id,
        )


@router.post(
    "/support/cases/{case_id}/reply-result",
    response_model=BotSupportReplyResultResponse,
)
def complete_support_reply_from_bot(
    case_id: SupportCaseId,
    payload: BotSupportReplyResultRequest,
    x_bot_token: str | None = Header(default=None),
) -> BotSupportReplyResultResponse:
    _check_bot_token(x_bot_token)
    _check_support_admin(payload.admin_telegram_user_id)
    with get_session_context() as db:
        recorded = complete_support_reply(
            db,
            case_id=case_id,
            admin_telegram_user_id=payload.admin_telegram_user_id,
            reply_message_id=payload.reply_message_id,
            outcome=payload.outcome,
        )
        if not recorded:
            raise HTTPException(status_code=409, detail="Support reply is not claimable")
        return BotSupportReplyResultResponse(status="recorded")


@router.post(
    "/news/drafts/{draft_id}/moderate",
    response_model=BotNewsModerationResponse,
)
def moderate_news_draft_from_bot(
    draft_id: NewsDraftId,
    payload: BotNewsModerationRequest,
    x_bot_token: str | None = Header(default=None),
) -> BotNewsModerationResponse:
    _check_bot_token(x_bot_token)
    _check_support_admin(payload.admin_telegram_user_id)
    with get_session_context() as db:
        result = moderate_draft(
            db,
            draft_id=draft_id,
            admin_telegram_user_id=payload.admin_telegram_user_id,
            action=payload.action,
        )
        return BotNewsModerationResponse(
            status=result.status,
            cluster_status=result.cluster_status,
        )
