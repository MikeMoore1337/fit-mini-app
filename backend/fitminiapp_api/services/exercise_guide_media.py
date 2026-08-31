from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

MEDIA_ROOT = Path(__file__).resolve().parents[2] / "assets" / "exercise-guides"
MANIFEST_PATH = MEDIA_ROOT / "manifest.json"


@lru_cache(maxsize=1)
def _manifest() -> dict:
    payload = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if payload.get("schema_version") not in {1, 2}:
        raise RuntimeError("Unsupported exercise guide media manifest version")
    return payload


def _public_url(path: str) -> str:
    return f"/static/exercise-guides/{path}"


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
    result = []
    for media in sorted(item["media"], key=lambda value: value["sort_order"]):
        sources = media.get("sources") or [
            {
                "path": media["path"],
                "mime_type": "image/jpeg" if media["path"].endswith(".jpg") else "image/svg+xml",
                "width": media["width"],
                "height": media["height"],
                "byte_size": media["byte_size"],
            }
        ]
        result.append(
            {
                "type": media["type"],
                "url": _public_url(media["path"]),
                "poster": _public_url(media["poster_path"]),
                "phase_id": media["phase_id"],
                "phase": media["phase"],
                "alt": media.get("alt", f"{exercise_title}: {media['phase'].lower()}"),
                "asset_id": media.get("asset_id"),
                "asset_version": media.get("asset_version"),
                "variant_key": media.get("variant_key"),
                "source_name": source_name,
                "source_url": source_url,
                "source_license": source_license,
                "source_license_url": source_license_url,
                "width": media["width"],
                "height": media["height"],
                "byte_size": media["byte_size"],
                "sort_order": media["sort_order"],
                "sources": [
                    {
                        "url": _public_url(source["path"]),
                        "mime_type": source["mime_type"],
                        "width": source["width"],
                        "height": source["height"],
                        "byte_size": source["byte_size"],
                    }
                    for source in sorted(sources, key=lambda value: value["width"])
                ],
            }
        )
    return result
