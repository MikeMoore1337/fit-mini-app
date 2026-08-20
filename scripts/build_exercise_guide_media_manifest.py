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
    "positive": "Позитивная фаза",
    "negative": "Негативная фаза",
    "setup": "Подготовка",
    "hold": "Удержание",
    "cycle_one": "Первая фаза цикла",
    "cycle_two": "Вторая фаза цикла",
    "sequence_start": "Начало последовательности",
    "sequence_next": "Следующая позиция",
    "technique": "Техника движения",
}

# The upstream images are ordered as two positions, not as physiological phases.
# Their direction differs even inside one exercise family: for example, the
# barbell bench press starts at lockout, while the machine press starts at the
# chest. Keep the mapping explicit so the caption describes the movement that
# begins in the shown position instead of blindly renaming start/active files.
NEGATIVE_FIRST_SLUGS = {
    "ab-wheel",
    "bench-dip",
    "bench-press",
    "belt-squat",
    "bulgarian-split-squat",
    "chest-dip",
    "dumbbell-fly",
    "dumbbell-overhead-extension",
    "dumbbell-pullover",
    "front-squat",
    "goblet-squat",
    "good-morning",
    "hack-squat",
    "incline-bench-press",
    "incline-dumbbell-fly",
    "kettlebell-goblet-squat",
    "kettlebell-swing",
    "leg-press",
    "lunge",
    "lying-dumbbell-triceps-extension",
    "nordic-curl",
    "overhead-press",
    "overhead-triceps-extension",
    "pec-deck",
    "push-up",
    "reverse-lunge",
    "romanian-deadlift",
    "seated-dumbbell-press",
    "single-leg-rdl",
    "sissy-squat",
    "skull-crusher",
    "smith-squat",
    "split-squat",
    "squat",
    "step-up",
    "walking-lunge",
    "wall-sit",
    "weighted-dip",
}

POSITIVE_FIRST_SLUGS = {
    "arnold-press",
    "barbell-curl",
    "barbell-glute-bridge",
    "barbell-row",
    "barbell-shrug",
    "box-jump",
    "burpee",
    "cable-curl",
    "cable-fly",
    "cable-kickback",
    "cable-lateral-raise",
    "cable-pull-through",
    "cable-pushdown",
    "cable-row-one-arm",
    "cable-crunch",
    "calf-press",
    "captain-chair-leg-raise",
    "chin-up",
    "chest-supported-row",
    "close-grip-bench-press",
    "close-grip-lat-pulldown",
    "concentration-curl",
    "crunch",
    "deadlift",
    "decline-bench-press",
    "decline-dumbbell-press",
    "donkey-calf-raise",
    "dumbbell-bench-press",
    "dumbbell-curl",
    "dumbbell-front-raise",
    "dumbbell-lateral-raise",
    "dumbbell-shrug",
    "ez-bar-curl",
    "face-pull",
    "glute-ham-raise",
    "hammer-curl",
    "hanging-leg-raise",
    "hip-abduction",
    "hip-adduction",
    "hip-thrust",
    "hyperextension",
    "incline-dumbbell-press",
    "incline-dumbbell-curl",
    "inverted-row",
    "landmine-press",
    "lat-pulldown",
    "leg-curl",
    "leg-extension",
    "low-to-high-cable-fly",
    "machine-biceps-curl",
    "machine-chest-press",
    "machine-dip",
    "machine-lateral-raise",
    "machine-row",
    "machine-shoulder-press",
    "meadows-row",
    "medicine-ball-slam",
    "mountain-climber",
    "one-arm-dumbbell-row",
    "pallof-press",
    "pendlay-row",
    "preacher-curl",
    "pull-up",
    "rack-pull",
    "rear-delt-fly",
    "renegade-row",
    "reverse-curl",
    "reverse-crunch",
    "reverse-grip-lat-pulldown",
    "reverse-pec-deck",
    "rope-pushdown",
    "rowing-machine",
    "russian-twist",
    "seated-cable-row",
    "seated-calf-raise",
    "seated-leg-curl",
    "single-arm-cable-triceps-extension",
    "single-leg-calf-raise",
    "single-leg-hip-thrust",
    "smith-bench-press",
    "smith-shoulder-press",
    "spider-curl",
    "standing-calf-raise",
    "standing-leg-curl",
    "stiff-leg-deadlift",
    "straight-arm-pulldown",
    "sumo-deadlift",
    "t-bar-row",
    "thruster",
    "triceps-kickback",
    "upright-row",
    "wall-ball",
    "woodchopper",
    "y-raise",
    "kettlebell-clean",
    "kettlebell-snatch",
}

SPECIAL_PHASES_BY_SLUG = {
    "plank": ("setup", "hold"),
    "side-plank": ("setup", "hold"),
    "hollow-hold": ("setup", "hold"),
    "dead-bug": ("setup", "hold"),
    "bird-dog": ("setup", "hold"),
    "farmer-walk": ("cycle_one", "cycle_two"),
    "suitcase-carry": ("cycle_one", "cycle_two"),
    "treadmill-run": ("cycle_one", "cycle_two"),
    "jump-rope": ("cycle_one", "cycle_two"),
    "assault-bike": ("cycle_one", "cycle_two"),
    "battle-rope": ("cycle_one", "cycle_two"),
    "sled-push": ("cycle_one", "cycle_two"),
    "sled-pull": ("cycle_one", "cycle_two"),
    "bear-crawl": ("cycle_one", "cycle_two"),
    "turkish-get-up": ("sequence_start", "sequence_next"),
}


def phase_ids_for_slug(slug: str) -> tuple[str, str]:
    if slug in NEGATIVE_FIRST_SLUGS:
        return "negative", "positive"
    if slug in POSITIVE_FIRST_SLUGS:
        return "positive", "negative"
    if phases := SPECIAL_PHASES_BY_SLUG.get(slug):
        return phases
    raise ValueError(f"Exercise {slug} has no reviewed phase mapping")


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

    reviewed_slugs = NEGATIVE_FIRST_SLUGS | POSITIVE_FIRST_SLUGS | set(SPECIAL_PHASES_BY_SLUG)
    source_slugs = set(SOURCE_EXERCISES)
    if reviewed_slugs != source_slugs:
        missing = sorted(source_slugs - reviewed_slugs)
        unexpected = sorted(reviewed_slugs - source_slugs)
        raise ValueError(
            "Exercise phase mapping mismatch "
            f"(missing={missing or 'none'}, unexpected={unexpected or 'none'})"
        )

    result = {}
    for slug in SOURCE_EXERCISES:
        start_phase, active_phase = phase_ids_for_slug(slug)
        files = [
            (f"{slug}-start.jpg", start_phase),
            (f"{slug}-active.jpg", active_phase),
        ]
        if {start_phase, active_phase} == {"positive", "negative"}:
            files.sort(key=lambda item: item[1] != "positive")
        result[slug] = files
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
