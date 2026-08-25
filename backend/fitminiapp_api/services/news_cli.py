from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import urlparse

from fitminiapp_api.db.session import get_session_context
from fitminiapp_api.services.news_sources import apply_source_allowlist, parse_source_allowlist

MAX_ALLOWLIST_BYTES = 1_048_576


def _definitions(path: Path):
    if not path.is_file() or path.stat().st_size > MAX_ALLOWLIST_BYTES:
        raise ValueError("allowlist file is missing or too large")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("allowlist file is not valid UTF-8 JSON") from exc
    return parse_source_allowlist(raw)


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage the Telegram news source allowlist")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("check", "apply"):
        command_parser = subparsers.add_parser(command)
        command_parser.add_argument("path", type=Path)
        if command == "apply":
            command_parser.add_argument("--disable-missing", action="store_true")
    args = parser.parse_args()
    try:
        definitions = _definitions(args.path)
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
