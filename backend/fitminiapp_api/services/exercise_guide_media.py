from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

MEDIA_ROOT = Path(__file__).resolve().parents[2] / "assets" / "exercise-guides"
MANIFEST_PATH = MEDIA_ROOT / "manifest.json"


@lru_cache(maxsize=1)
def _manifest() -> dict:
    payload = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1:
        raise RuntimeError("Unsupported exercise guide media manifest version")
    return payload


def get_guide_media(
    slug: str,
    *,
    exercise_title: str,
    source_name: str,
    source_url: str,
    source_license: str,
    source_license_url: str | None,
) -> list[dict]:
    item = _manifest()["exercises"].get(slug)
    if item is None:
        return []
    return [
        {
            "type": media["type"],
            "url": f"/static/exercise-guides/{media['path']}",
            "poster": f"/static/exercise-guides/{media['poster_path']}",
            "phase": media["phase"],
            "alt": f"{exercise_title}: {media['phase'].lower()}",
            "source_name": source_name,
            "source_url": source_url,
            "source_license": source_license,
            "source_license_url": source_license_url,
            "width": media["width"],
            "height": media["height"],
            "byte_size": media["byte_size"],
            "sort_order": media["sort_order"],
        }
        for media in sorted(item["media"], key=lambda value: value["sort_order"])
    ]
