from __future__ import annotations

import base64
import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta

from cryptography.fernet import Fernet, InvalidToken

from fitminiapp_api.core.config import settings
from fitminiapp_api.schemas.progress import NutritionReportPeriod

PROGRESS_REPORT_DOWNLOAD_TTL = timedelta(minutes=5)
_TOKEN_CONTEXT = b"yfc-progress-report-download-v1"


@dataclass(frozen=True)
class ProgressReportDownloadGrant:
    actor_user_id: int
    subject_user_id: int
    subject_role: str
    period: NutritionReportPeriod
    date_from: date | None
    date_to: date | None


def _fernet() -> Fernet:
    digest = hashlib.sha256(settings.secret_key.encode("utf-8") + _TOKEN_CONTEXT).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def create_progress_report_download_token(
    *,
    actor_user_id: int,
    subject_user_id: int,
    subject_role: str,
    period: NutritionReportPeriod,
    date_from: date | None,
    date_to: date | None,
) -> tuple[str, datetime]:
    payload = {
        "actor": actor_user_id,
        "subject": subject_user_id,
        "role": subject_role,
        "period": period.value,
        "date_from": date_from.isoformat() if date_from else None,
        "date_to": date_to.isoformat() if date_to else None,
    }
    token = _fernet().encrypt(
        json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    )
    return token.decode("ascii"), datetime.now(UTC) + PROGRESS_REPORT_DOWNLOAD_TTL


def read_progress_report_download_token(token: str) -> ProgressReportDownloadGrant | None:
    try:
        raw = _fernet().decrypt(
            token.encode("ascii"), ttl=int(PROGRESS_REPORT_DOWNLOAD_TTL.total_seconds())
        )
        payload = json.loads(raw)
        return ProgressReportDownloadGrant(
            actor_user_id=int(payload["actor"]),
            subject_user_id=int(payload["subject"]),
            subject_role=str(payload["role"]),
            period=NutritionReportPeriod(payload["period"]),
            date_from=date.fromisoformat(payload["date_from"]) if payload["date_from"] else None,
            date_to=date.fromisoformat(payload["date_to"]) if payload["date_to"] else None,
        )
    except InvalidToken, UnicodeError, ValueError, TypeError, KeyError, json.JSONDecodeError:
        return None
