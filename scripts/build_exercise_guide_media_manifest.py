"""Build and validate the checked-in exercise guide media inventory.

The manifest is deliberately generated from local files. Production does not need
network access, Pillow, a CDN, or an external media API to render exercise guides.
"""

from __future__ import annotations

import argparse
import json
import sys
from functools import lru_cache
from pathlib import Path

from PIL import Image

ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
SOURCE_LICENSE_URL = "https://github.com/yuhonas/free-exercise-db/blob/main/LICENSE.md"
INTERNAL_SOURCE = {
    "name": "Your Fitness Coach",
    "url": "/",
    "license": "Иллюстрация создана для приложения",
    "license_url": None,
}
PHASES = {
    "start": "Исходное положение",
    "active": "Активная фаза",
    "technique": "Две фазы движения",
}


@lru_cache(maxsize=1)
def catalog_definition() -> tuple[
    dict[str, list[tuple[str, str]]], set[str], dict[str, str | None]
]:
    if str(BACKEND_DIR) not in sys.path:
        sys.path.insert(0, str(BACKEND_DIR))

    from fitminiapp_api.services.exercise_guides import (
        GENERATED_CARDIO_SLUGS,
        SOURCE_LICENSE,
        SOURCE_NAME,
        SOURCE_URL,
    )
    from sync_exercise_guide_assets import SOURCE_EXERCISES

    result = {
        slug: [
            (f"{slug}-start.jpg", "start"),
            (f"{slug}-active.jpg", "active"),
        ]
        for slug in SOURCE_EXERCISES
    }
    result.update(
        {slug: [(f"{slug}-technique.jpg", "technique")] for slug in GENERATED_CARDIO_SLUGS}
    )
    upstream_source = {
        "name": SOURCE_NAME,
        "url": SOURCE_URL,
        "license": SOURCE_LICENSE,
        "license_url": SOURCE_LICENSE_URL,
    }
    return result, GENERATED_CARDIO_SLUGS, upstream_source


def build_manifest(asset_dir: Path) -> dict:
    expected, generated_cardio_slugs, upstream_source = catalog_definition()
    expected_names = {name for files in expected.values() for name, _ in files}
    actual_names = {path.name for path in asset_dir.glob("*.jpg")}
    missing = sorted(expected_names - actual_names)
    unexpected = sorted(actual_names - expected_names)
    if missing or unexpected:
        details = []
        if missing:
            details.append("missing: " + ", ".join(missing))
        if unexpected:
            details.append("unexpected: " + ", ".join(unexpected))
        raise ValueError("Exercise guide asset inventory mismatch (" + "; ".join(details) + ")")

    exercises = {}
    for slug in sorted(expected):
        source = INTERNAL_SOURCE if slug in generated_cardio_slugs else upstream_source
        media = []
        for sort_order, (filename, phase_id) in enumerate(expected[slug]):
            path = asset_dir / filename
            with Image.open(path) as image:
                width, height = image.size
                image.verify()
            media.append(
                {
                    "type": "image",
                    "path": filename,
                    "poster_path": filename,
                    "phase_id": phase_id,
                    "phase": PHASES[phase_id],
                    "width": width,
                    "height": height,
                    "byte_size": path.stat().st_size,
                    "sort_order": sort_order,
                }
            )
        exercises[slug] = {"source": source, "media": media}

    return {
        "schema_version": 1,
        "default_pattern": "static-phases",
        "asset_count": sum(len(item["media"]) for item in exercises.values()),
        "total_bytes": sum(
            media["byte_size"] for item in exercises.values() for media in item["media"]
        ),
        "exercises": exercises,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--asset-dir",
        type=Path,
        default=ROOT_DIR / "backend" / "assets" / "exercise-guides",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT_DIR / "backend" / "assets" / "exercise-guides" / "manifest.json",
    )
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    manifest = build_manifest(args.asset_dir)
    rendered = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    if args.check:
        if not args.output.exists() or args.output.read_text(encoding="utf-8") != rendered:
            raise SystemExit(
                f"{args.output} is stale; run scripts/build_exercise_guide_media_manifest.py"
            )
        print(
            f"Validated {manifest['asset_count']} assets "
            f"({manifest['total_bytes']} bytes) for {len(manifest['exercises'])} exercises"
        )
        return

    args.output.write_text(rendered, encoding="utf-8")
    print(
        f"Wrote {manifest['asset_count']} assets "
        f"({manifest['total_bytes']} bytes) for {len(manifest['exercises'])} exercises"
    )


if __name__ == "__main__":
    main()
