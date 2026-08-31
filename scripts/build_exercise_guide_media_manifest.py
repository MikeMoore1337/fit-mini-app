"""Build and validate the checked-in exercise guide media inventory.

The manifest is deliberately generated from local files. Production does not need
network access, Pillow, a CDN, or an external media API to render exercise guides.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from functools import lru_cache
from pathlib import Path

from PIL import Image

from build_exercise_human_visual_assets import (
    ASSET_VERSION,
    HUMAN_VISUAL_SPECS,
)
from build_exercise_human_visual_assets import (
    PHASES as HUMAN_PHASES,
)

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
]:
    if str(BACKEND_DIR) not in sys.path:
        sys.path.insert(0, str(BACKEND_DIR))

    from fitminiapp_api.services.exercise_catalog_metadata import (
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
    if set(YFC_ORIGINAL_VECTOR_SLUGS) != set(HUMAN_VISUAL_SPECS):
        raise ValueError("Task 120E visual specs do not cover the full YFC machine batch")
    for slug in YFC_ORIGINAL_VECTOR_SLUGS:
        result[slug] = [
            (f"human-v1/{slug}/{phase_id}-480w.webp", phase_id) for phase_id in HUMAN_PHASES
        ]
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
    )


def _load_human_review(review_lock: Path) -> dict:
    payload = json.loads(review_lock.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1 or payload.get("asset_version") != ASSET_VERSION:
        raise ValueError("Unsupported Task 120E review lock")
    if payload.get("owner_gates", {}).get("gate_a", {}).get("status") != "approved":
        raise ValueError("Task 120E Gate A is not recorded as approved")
    if set(payload.get("exercises", {})) != set(HUMAN_VISUAL_SPECS):
        raise ValueError("Task 120E review lock exercise coverage mismatch")
    return payload


def build_manifest(asset_dir: Path, review_lock: Path) -> dict:
    (
        expected,
        generated_cardio_slugs,
        upstream_source,
        media_alt_by_phase,
    ) = catalog_definition()
    human_review = _load_human_review(review_lock)
    expected_paths = {
        name for files in expected.values() for name, _ in files if not name.startswith("human-v1/")
    }
    for exercise in human_review["exercises"].values():
        for phase in exercise["phases"].values():
            expected_paths.update(source["path"] for source in phase["sources"])
    actual_paths = {
        path.relative_to(asset_dir).as_posix()
        for pattern in ("*.jpg", "*.webp", "*.svg")
        for path in asset_dir.rglob(pattern)
    }
    missing = sorted(expected_paths - actual_paths)
    unexpected = sorted(actual_paths - expected_paths)
    if missing or unexpected:
        details = []
        if missing:
            details.append("missing: " + ", ".join(missing))
        if unexpected:
            details.append("unexpected: " + ", ".join(unexpected))
        raise ValueError("Exercise guide asset inventory mismatch (" + "; ".join(details) + ")")

    exercises = {}
    human_hashes: dict[str, str] = {}
    for slug in sorted(expected):
        if slug in HUMAN_VISUAL_SPECS:
            review_exercise = human_review["exercises"][slug]
            source = {
                "source_kind": "yfc_ai_generated",
                "name": "Your Fitness Coach",
                "url": "/",
                "source_revision_or_retrieved_at": human_review["created_at"],
                "license": "Иллюстрация создана для приложения",
                "license_url": None,
                "license_url_or_local_notice": human_review["rights"]["local_notice"],
                "origin": human_review["origin"],
                "asset_type": human_review["asset_type"],
                "asset_version": human_review["asset_version"],
                "variant_key": review_exercise["variant_key"],
                "generation": human_review["generation"],
                "rights": human_review["rights"],
                "owner_gates": human_review["owner_gates"],
            }
        else:
            source = INTERNAL_SOURCE if slug in generated_cardio_slugs else upstream_source
        media = []
        for sort_order, (filename, phase_id) in enumerate(expected[slug]):
            path = asset_dir / filename
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
            if slug in HUMAN_VISUAL_SPECS:
                locked_phase = human_review["exercises"][slug]["phases"][phase_id]
                locked_sources = locked_phase["sources"]
                for locked_source in locked_sources:
                    source_path = asset_dir / locked_source["path"]
                    if source_path.stat().st_size != locked_source["byte_size"]:
                        raise ValueError(f"Byte-size mismatch: {source_path}")
                    with Image.open(source_path) as derivative:
                        derivative.load()
                        if derivative.size != (
                            locked_source["width"],
                            locked_source["height"],
                        ):
                            raise ValueError(f"Dimension mismatch: {source_path}")
                    digest = hashlib.sha256(source_path.read_bytes()).hexdigest()
                    if digest != locked_source["sha256"]:
                        raise ValueError(f"SHA-256 mismatch: {source_path}")
                    if previous := human_hashes.get(digest):
                        raise ValueError(
                            f"Duplicate Task 120E derivative hash: {previous}, {source_path}"
                        )
                    human_hashes[digest] = source_path.as_posix()
                mobile_source = next(source for source in locked_sources if source["width"] == 480)
                if mobile_source["byte_size"] > 160 * 1024:
                    raise ValueError(f"Mobile phase exceeds 160 KB: {slug}/{phase_id}")
                variant_key = human_review["exercises"][slug]["variant_key"]
                media_item.update(
                    {
                        "asset_id": f"{slug}:{variant_key}:{phase_id}:{ASSET_VERSION}",
                        "asset_version": ASSET_VERSION,
                        "variant_key": variant_key,
                        "asset_type": human_review["asset_type"],
                        "origin": human_review["origin"],
                        "source_master_sha256": locked_phase["source_master_sha256"],
                        "asset_sha256": mobile_source["sha256"],
                        "sources": locked_sources,
                        "reviews": locked_phase["reviews"],
                    }
                )
            elif slug in media_alt_by_phase:
                media_item["asset_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
            if alt := media_alt_by_phase.get(slug, {}).get(phase_id):
                media_item["alt"] = alt
            media.append(media_item)
        exercises[slug] = {"source": source, "media": media}

        if slug in HUMAN_VISUAL_SPECS:
            mobile_pair_bytes = sum(
                next(source for source in item["sources"] if source["width"] == 480)["byte_size"]
                for item in media
            )
            if mobile_pair_bytes > 320 * 1024:
                raise ValueError(f"Mobile pair exceeds 320 KB: {slug}")

    return {
        "schema_version": 2,
        "default_pattern": "static-phases",
        "asset_count": sum(len(item["media"]) for item in exercises.values()),
        "derivative_count": len(expected_paths),
        "total_bytes": sum((asset_dir / path).stat().st_size for path in expected_paths),
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
    parser.add_argument(
        "--review-lock",
        type=Path,
        default=ROOT_DIR / "docs" / "exercises" / "catalog-v2" / "120E_ASSET_REVIEW.json",
    )
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    manifest = build_manifest(args.asset_dir, args.review_lock)
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
