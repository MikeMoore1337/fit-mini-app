from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import urlparse

from fitminiapp_api.core.config import settings
from fitminiapp_api.db.session import get_session_context
from fitminiapp_api.services.news_rescore import rescore_freshness_blocked_clusters
from fitminiapp_api.services.news_sources import apply_source_allowlist, load_source_allowlist


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage the Telegram news pipeline")
    subparsers = parser.add_subparsers(dest="command", required=True)

    check_parser = subparsers.add_parser("check")
    check_parser.add_argument("path", type=Path)

    apply_parser = subparsers.add_parser("apply")
    apply_parser.add_argument("path", type=Path)
    apply_parser.add_argument("--disable-missing", action="store_true")

    subparsers.add_parser(
        "rescore-freshness",
        help="Re-score stored clustered news blocked by the previous freshness window",
    )

    args = parser.parse_args()
    if args.command == "rescore-freshness":
        with get_session_context() as db:
            promoted = rescore_freshness_blocked_clusters(
                db,
                candidate_threshold=settings.news_candidate_score_threshold,
            )
        print(json.dumps({"status": "rescored", "promoted": promoted}))
        return

    try:
        definitions = load_source_allowlist(args.path)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    safe_summary = [
        {
            "id": item.id,
            "name": item.name,
            "host": urlparse(item.url).hostname,
            "type": item.source_type,
            "fetch_kind": item.fetch_kind,
            "enabled": item.enabled,
        }
        for item in definitions
    ]
    if args.command == "check":
        print(json.dumps({"status": "valid", "sources": safe_summary}, ensure_ascii=False))
        return
    with get_session_context() as db:
        created, updated = apply_source_allowlist(
            db,
            definitions,
            disable_missing=args.disable_missing,
        )
    print(
        json.dumps(
            {
                "status": "applied",
                "created": created,
                "updated": updated,
                "sources": safe_summary,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
