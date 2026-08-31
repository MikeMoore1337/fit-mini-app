"""Build and validate the checked-in exercise guide media inventory.

The manifest is deliberately generated from local files. Production does not need
network access, Pillow, a CDN, or an external media API to render exercise guides.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import xml.etree.ElementTree as ET
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
VECTOR_SOURCE = {
    "source_kind": "yfc_original",
    "name": "Your Fitness Coach",
    "url": "/",
    "source_revision_or_retrieved_at": "2026-08-31",
    "license": "Иллюстрация создана для приложения",
    "license_url": None,
    "license_url_or_local_notice": "backend/assets/exercise-guides/NOTICE.md",
    "author_or_generator_record": "scripts/build_upper_body_machine_guide_assets.py@Task-120B",
    "reviewer": "fitness-domain-reviewer / Task 120B",
    "reviewed_at": "2026-08-31",
    "commercial_use_verified": True,
    "redistribution_verified": True,
    "modification_verified": True,
    "semantic_identity_verified": True,
    "setup_verified": True,
    "key_positions_verified": True,
}
LOWER_BODY_VECTOR_SOURCE = {
    **VECTOR_SOURCE,
    "author_or_generator_record": "scripts/build_lower_body_machine_guide_assets.py@Task-120C",
    "reviewer": "fitness-domain-reviewer / Task 120C",
}
PHASES = {
    "concentric_end": "Фаза усилия",
    "eccentric_end": "Фаза возврата",
    "setup": "Подготовка",
    "hold": "Удержание",
    "work": "Рабочее положение",
    "cycle_one": "Первое положение",
    "cycle_two": "Второе положение",
    "sequence_start": "Начало движения",
    "sequence_next": "Следующая позиция",
    "technique": "Техника движения",
}

# A still image is a position, not a physiological muscle action. For dynamic
# strength exercises the caption describes the movement completed in the shown
# position. The mapping is explicit because upstream image order differs even
# inside one family: the barbell bench press starts at lockout, while the
# machine press starts at the chest.
CONCENTRIC_END_IN_START_IMAGE_SLUGS = {
    "ab-wheel",
    "bench-dip",
    "bench-press",
    "belt-squat",
    "bulgarian-split-squat",
    "chest-dip",
    "dumbbell-fly",
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
    "nordic-curl",
    "overhead-press",
    "pec-deck",
    "push-up",
    "reverse-lunge",
    "seated-dumbbell-press",
    "single-leg-rdl",
    "sissy-squat",
    "skull-crusher",
    "split-squat",
    "squat",
    "triceps-kickback",
    "upright-row",
    "weighted-dip",
    "hyperextension",
}

ECCENTRIC_END_IN_START_IMAGE_SLUGS = {
    "arnold-press",
    "barbell-curl",
    "barbell-glute-bridge",
    "barbell-row",
    "barbell-shrug",
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
    "machine-incline-chest-press",
    "independent-lever-chest-press",
    "machine-decline-chest-press",
    "machine-dip",
    "machine-lateral-raise",
    "machine-row",
    "lever-high-row",
    "lever-low-row",
    "independent-lever-lat-pulldown",
    "machine-pullover",
    "chest-supported-dumbbell-row",
    "machine-shoulder-press",
    "independent-lever-shoulder-press",
    "machine-triceps-extension",
    "machine-glute-kickback",
    "machine-hip-thrust",
    "meadows-row",
    "one-arm-dumbbell-row",
    "pendlay-row",
    "pendulum-squat",
    "plate-loaded-leg-press",
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
    "seated-cable-row",
    "seated-calf-raise",
    "seated-leg-curl",
    "single-arm-cable-triceps-extension",
    "single-leg-calf-raise",
    "single-leg-hip-thrust",
    "smith-bench-press",
    "smith-shoulder-press",
    "smith-split-squat",
    "spider-curl",
    "standing-calf-raise",
    "standing-leg-curl",
    "stiff-leg-deadlift",
    "straight-arm-pulldown",
    "sumo-deadlift",
    "t-bar-row",
    "woodchopper",
    "y-raise",
    "dumbbell-overhead-extension",
    "lying-dumbbell-triceps-extension",
    "romanian-deadlift",
    "smith-squat",
    "unilateral-leg-press",
    "v-squat-machine",
    "reverse-hyperextension",
}

SPECIAL_PHASES_BY_SLUG = {
    "plank": ("setup", "hold"),
    "side-plank": ("setup", "hold"),
    "hollow-hold": ("setup", "hold"),
    "wall-sit": ("setup", "hold"),
    "pallof-press": ("setup", "hold"),
    "overhead-triceps-extension": ("setup", "hold"),
    "dead-bug": ("setup", "work"),
    "bird-dog": ("setup", "work"),
    "box-jump": ("setup", "work"),
    "burpee": ("sequence_start", "sequence_next"),
    "kettlebell-clean": ("sequence_start", "sequence_next"),
    "kettlebell-snatch": ("sequence_start", "sequence_next"),
    "medicine-ball-slam": ("sequence_start", "sequence_next"),
    "step-up": ("sequence_start", "sequence_next"),
    "thruster": ("sequence_start", "sequence_next"),
    "wall-ball": ("sequence_start", "sequence_next"),
    "farmer-walk": ("cycle_one", "cycle_two"),
    "suitcase-carry": ("cycle_one", "cycle_two"),
    "treadmill-run": ("cycle_one", "cycle_two"),
    "jump-rope": ("cycle_one", "cycle_two"),
    "assault-bike": ("cycle_one", "cycle_two"),
    "battle-rope": ("cycle_one", "cycle_two"),
    "sled-push": ("cycle_one", "cycle_two"),
    "sled-pull": ("cycle_one", "cycle_two"),
    "bear-crawl": ("cycle_one", "cycle_two"),
    "mountain-climber": ("cycle_one", "cycle_two"),
    "rowing-machine": ("cycle_one", "cycle_two"),
    "russian-twist": ("cycle_one", "cycle_two"),
    "walking-lunge": ("cycle_one", "cycle_two"),
    "turkish-get-up": ("sequence_start", "sequence_next"),
}


def phase_ids_for_slug(slug: str) -> tuple[str, str]:
    if slug in CONCENTRIC_END_IN_START_IMAGE_SLUGS:
        return "concentric_end", "eccentric_end"
    if slug in ECCENTRIC_END_IN_START_IMAGE_SLUGS:
        return "eccentric_end", "concentric_end"
    if phases := SPECIAL_PHASES_BY_SLUG.get(slug):
        return phases
    raise ValueError(f"Exercise {slug} has no reviewed phase mapping")


@lru_cache(maxsize=1)
def catalog_definition() -> tuple[
    dict[str, list[tuple[str, str]]],
    set[str],
    dict[str, str | None],
    dict[str, dict[str, str]],
    set[str],
]:
    if str(BACKEND_DIR) not in sys.path:
        sys.path.insert(0, str(BACKEND_DIR))

    from fitminiapp_api.services.exercise_catalog_metadata import (
        LOWER_BODY_MACHINE_SLUGS,
        MEDIA_ALT_BY_PHASE,
    )
    from fitminiapp_api.services.exercise_guides import (
        GENERATED_CARDIO_SLUGS,
        SOURCE_LICENSE,
        SOURCE_NAME,
        SOURCE_URL,
        YFC_ORIGINAL_VECTOR_SLUGS,
    )
    from sync_exercise_guide_assets import SOURCE_EXERCISES

    phase_groups = (
        CONCENTRIC_END_IN_START_IMAGE_SLUGS,
        ECCENTRIC_END_IN_START_IMAGE_SLUGS,
        set(SPECIAL_PHASES_BY_SLUG),
    )
    overlaps = sorted(
        slug
        for index, group in enumerate(phase_groups)
        for other_group in phase_groups[index + 1 :]
        for slug in group & other_group
    )
    if overlaps:
        raise ValueError(f"Exercise phase mappings overlap: {overlaps}")

    reviewed_slugs = (
        CONCENTRIC_END_IN_START_IMAGE_SLUGS
        | ECCENTRIC_END_IN_START_IMAGE_SLUGS
        | set(SPECIAL_PHASES_BY_SLUG)
    )
    source_slugs = set(SOURCE_EXERCISES)
    expected_reviewed_slugs = source_slugs | set(YFC_ORIGINAL_VECTOR_SLUGS)
    if reviewed_slugs != expected_reviewed_slugs:
        missing = sorted(expected_reviewed_slugs - reviewed_slugs)
        unexpected = sorted(reviewed_slugs - expected_reviewed_slugs)
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
        if {start_phase, active_phase} == {"concentric_end", "eccentric_end"}:
            files.sort(key=lambda item: item[1] != "concentric_end")
        result[slug] = files
    for slug in YFC_ORIGINAL_VECTOR_SLUGS:
        start_phase, active_phase = phase_ids_for_slug(slug)
        files = [
            (f"{slug}-start.svg", start_phase),
            (f"{slug}-active.svg", active_phase),
        ]
        if {start_phase, active_phase} == {"concentric_end", "eccentric_end"}:
            files.sort(key=lambda item: item[1] != "concentric_end")
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
    return (
        result,
        GENERATED_CARDIO_SLUGS,
        upstream_source,
        MEDIA_ALT_BY_PHASE,
        set(LOWER_BODY_MACHINE_SLUGS),
    )


def build_manifest(asset_dir: Path) -> dict:
    (
        expected,
        generated_cardio_slugs,
        upstream_source,
        media_alt_by_phase,
        lower_body_vector_slugs,
    ) = catalog_definition()
    expected_names = {name for files in expected.values() for name, _ in files}
    actual_names = {path.name for pattern in ("*.jpg", "*.svg") for path in asset_dir.glob(pattern)}
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
        source = (
            INTERNAL_SOURCE
            if slug in generated_cardio_slugs
            else LOWER_BODY_VECTOR_SOURCE
            if slug in lower_body_vector_slugs
            else VECTOR_SOURCE
            if slug in media_alt_by_phase
            else upstream_source
        )
        media = []
        for sort_order, (filename, phase_id) in enumerate(expected[slug]):
            path = asset_dir / filename
            if path.suffix == ".svg":
                root = ET.parse(path).getroot()
                width = int(root.attrib["width"])
                height = int(root.attrib["height"])
            else:
                with Image.open(path) as image:
                    width, height = image.size
                    image.verify()
            media_item = {
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
            if slug in media_alt_by_phase:
                media_item["asset_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
            if alt := media_alt_by_phase.get(slug, {}).get(phase_id):
                media_item["alt"] = alt
            media.append(media_item)
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
