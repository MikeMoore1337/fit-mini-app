"""Download the public-domain two-phase exercise images used by the guide.

Source: https://github.com/yuhonas/free-exercise-db (Unlicense).
The checked-in assets are deliberately named after our stable exercise slugs so
the application never depends on GitHub at runtime.
"""

from __future__ import annotations

import argparse
import json
import re
import urllib.request
from pathlib import Path

DATASET_URL = "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/dist/exercises.json"
IMAGE_BASE_URL = "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises/"


# Our catalog intentionally uses short product-facing slugs. Values below are
# normalized upstream exercise ids (case and punctuation are ignored).
SOURCE_EXERCISES: dict[str, str] = {
    "bench-press": "barbell-bench-press-medium-grip",
    "incline-bench-press": "barbell-incline-bench-press-medium-grip",
    "decline-bench-press": "decline-barbell-bench-press",
    "close-grip-bench-press": "close-grip-barbell-bench-press",
    "dumbbell-bench-press": "dumbbell-bench-press",
    "incline-dumbbell-press": "incline-dumbbell-press",
    "decline-dumbbell-press": "decline-dumbbell-bench-press",
    "dumbbell-fly": "dumbbell-flyes",
    "incline-dumbbell-fly": "incline-dumbbell-flyes",
    "cable-fly": "cable-crossover",
    "low-to-high-cable-fly": "low-cable-crossover",
    "pec-deck": "butterfly",
    "machine-chest-press": "machine-bench-press",
    "smith-bench-press": "smith-machine-bench-press",
    "push-up": "pushups",
    "weighted-dip": "dips-chest-version",
    "chest-dip": "dips-chest-version",
    "dumbbell-pullover": "bent-arm-dumbbell-pullover",
    "deadlift": "barbell-deadlift",
    "rack-pull": "rack-pulls",
    "pull-up": "pullups",
    "chin-up": "chin-up",
    "lat-pulldown": "wide-grip-lat-pulldown",
    "reverse-grip-lat-pulldown": "underhand-cable-pulldowns",
    "close-grip-lat-pulldown": "close-grip-front-lat-pulldown",
    "straight-arm-pulldown": "straight-arm-pulldown",
    "barbell-row": "bent-over-barbell-row",
    "pendlay-row": "bent-over-barbell-row",
    "t-bar-row": "t-bar-row-with-handle",
    "one-arm-dumbbell-row": "one-arm-dumbbell-row",
    "chest-supported-row": "incline-bench-pull",
    "seated-cable-row": "seated-cable-rows",
    "machine-row": "leverage-iso-row",
    "inverted-row": "inverted-row",
    "meadows-row": "t-bar-row-with-handle",
    "cable-row-one-arm": "seated-one-arm-cable-pulley-rows",
    "hyperextension": "hyperextensions-back-extensions",
    "good-morning": "good-morning",
    "squat": "barbell-squat",
    "front-squat": "front-barbell-squat",
    "hack-squat": "hack-squat",
    "smith-squat": "smith-machine-squat",
    "goblet-squat": "goblet-squat",
    "belt-squat": "hack-squat",
    "leg-press": "leg-press",
    "lunge": "dumbbell-lunges",
    "walking-lunge": "bodyweight-walking-lunge",
    "reverse-lunge": "dumbbell-rear-lunge",
    "bulgarian-split-squat": "smith-single-leg-split-squat",
    "split-squat": "split-squats",
    "step-up": "dumbbell-step-ups",
    "leg-extension": "leg-extensions",
    "sissy-squat": "weighted-sissy-squat",
    "wall-sit": "bodyweight-squat",
    "romanian-deadlift": "romanian-deadlift",
    "stiff-leg-deadlift": "stiff-legged-barbell-deadlift",
    "single-leg-rdl": "kettlebell-one-legged-deadlift",
    "leg-curl": "lying-leg-curls",
    "seated-leg-curl": "seated-leg-curl",
    "standing-leg-curl": "standing-leg-curl",
    "nordic-curl": "natural-glute-ham-raise",
    "glute-ham-raise": "glute-ham-raise",
    "hip-thrust": "barbell-hip-thrust",
    "single-leg-hip-thrust": "single-leg-glute-bridge",
    "barbell-glute-bridge": "barbell-glute-bridge",
    "cable-pull-through": "pull-through",
    "kettlebell-swing": "one-arm-kettlebell-swings",
    "hip-abduction": "thigh-abductor",
    "hip-adduction": "thigh-adductor",
    "cable-kickback": "one-legged-cable-kickback",
    "sumo-deadlift": "sumo-deadlift",
    "overhead-press": "barbell-shoulder-press",
    "seated-dumbbell-press": "seated-dumbbell-press",
    "arnold-press": "arnold-dumbbell-press",
    "machine-shoulder-press": "machine-shoulder-military-press",
    "smith-shoulder-press": "smith-machine-overhead-shoulder-press",
    "landmine-press": "landmine-linear-jammer",
    "dumbbell-lateral-raise": "side-lateral-raise",
    "cable-lateral-raise": "cable-seated-lateral-raise",
    "machine-lateral-raise": "seated-side-lateral-raise",
    "dumbbell-front-raise": "front-dumbbell-raise",
    "rear-delt-fly": "dumbbell-lying-rear-lateral-raise",
    "reverse-pec-deck": "reverse-machine-flyes",
    "face-pull": "face-pull",
    "upright-row": "upright-barbell-row",
    "barbell-shrug": "barbell-shrug",
    "dumbbell-shrug": "dumbbell-shrug",
    "y-raise": "front-incline-dumbbell-raise",
    "barbell-curl": "barbell-curl",
    "ez-bar-curl": "ez-bar-curl",
    "dumbbell-curl": "dumbbell-bicep-curl",
    "hammer-curl": "hammer-curls",
    "incline-dumbbell-curl": "incline-dumbbell-curl",
    "preacher-curl": "preacher-curl",
    "cable-curl": "high-cable-curls",
    "concentration-curl": "concentration-curls",
    "reverse-curl": "reverse-barbell-curl",
    "spider-curl": "spider-curl",
    "machine-biceps-curl": "machine-bicep-curl",
    "skull-crusher": "ez-bar-skullcrusher",
    "rope-pushdown": "triceps-pushdown-rope-attachment",
    "cable-pushdown": "triceps-pushdown",
    "overhead-triceps-extension": "overhead-triceps",
    "dumbbell-overhead-extension": "seated-triceps-press",
    "lying-dumbbell-triceps-extension": "lying-dumbbell-tricep-extension",
    "bench-dip": "bench-dips",
    "triceps-kickback": "tricep-dumbbell-kickback",
    "machine-dip": "dip-machine",
    "single-arm-cable-triceps-extension": "low-cable-triceps-extension",
    "standing-calf-raise": "standing-calf-raises",
    "seated-calf-raise": "seated-calf-raise",
    "donkey-calf-raise": "donkey-calf-raises",
    "calf-press": "calf-press",
    "single-leg-calf-raise": "standing-calf-raises",
    "plank": "plank",
    "side-plank": "side-bridge",
    "crunch": "crunches",
    "reverse-crunch": "reverse-crunch",
    "cable-crunch": "cable-crunch",
    "hanging-leg-raise": "hanging-leg-raise",
    "captain-chair-leg-raise": "hanging-leg-raise",
    "ab-wheel": "ab-roller",
    "russian-twist": "russian-twist",
    "pallof-press": "pallof-press",
    "woodchopper": "standing-cable-wood-chop",
    "mountain-climber": "mountain-climbers",
    "hollow-hold": "plank",
    "dead-bug": "dead-bug",
    "bird-dog": "superman",
    "burpee": "body-up",
    "box-jump": "front-box-jump",
    "jump-rope": "rope-jumping",
    "rowing-machine": "rowing-stationary",
    "treadmill-run": "running-treadmill",
    "assault-bike": "air-bike",
    "battle-rope": "battling-ropes",
    "sled-push": "sled-push",
    "sled-pull": "sled-drag-harness",
    "farmer-walk": "farmers-walk",
    "suitcase-carry": "rickshaw-carry",
    "medicine-ball-slam": "one-arm-medicine-ball-slam",
    "wall-ball": "medicine-ball-chest-pass",
    "thruster": "kettlebell-thruster",
    "kettlebell-clean": "kettlebell-hang-clean",
    "kettlebell-snatch": "one-arm-kettlebell-snatch",
    "kettlebell-goblet-squat": "goblet-squat",
    "turkish-get-up": "kettlebell-turkish-get-up-lunge-style",
    "renegade-row": "alternating-renegade-row",
    "bear-crawl": "bear-crawl-sled-drags",
}


def normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def load_dataset(path: Path | None) -> list[dict]:
    if path is not None:
        return json.loads(path.read_text(encoding="utf-8"))
    with urllib.request.urlopen(DATASET_URL) as response:
        return json.load(response)


def download(url: str, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url) as response:
        target.write_bytes(response.read())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("backend/assets/exercise-guides"),
    )
    parser.add_argument("--slug", choices=sorted(SOURCE_EXERCISES))
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    dataset = load_dataset(args.dataset)
    by_id = {normalize(item["id"]): item for item in dataset}
    missing = sorted(set(SOURCE_EXERCISES.values()) - set(by_id))
    if missing:
        raise SystemExit("Unknown upstream exercise ids: " + ", ".join(missing))

    selected = {
        slug: source_id
        for slug, source_id in SOURCE_EXERCISES.items()
        if args.slug is None or slug == args.slug
    }
    for index, (slug, source_id) in enumerate(selected.items(), start=1):
        item = by_id[source_id]
        images = item.get("images") or []
        if len(images) < 2:
            raise SystemExit(f"Exercise {item['id']} does not have two images")
        for phase, image_path in zip(("start", "active"), images[:2], strict=True):
            suffix = Path(image_path).suffix.lower() or ".jpg"
            target = args.output / f"{slug}-{phase}{suffix}"
            if args.force or not target.exists():
                download(IMAGE_BASE_URL + image_path, target)
        print(f"[{index:03}/{len(selected)}] {slug} <- {item['id']}")


if __name__ == "__main__":
    main()
