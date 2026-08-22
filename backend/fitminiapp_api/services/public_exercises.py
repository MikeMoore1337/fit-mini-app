from __future__ import annotations

from functools import lru_cache

from fitminiapp_api.services.exercise_guides import (
    DEFAULT_SAFETY_NOTES,
    PROFILES,
    SLUG_TO_PROFILE,
    SOURCE_LICENSE,
    SOURCE_LICENSE_URL,
    SOURCE_NAME,
    SOURCE_URL,
)
from fitminiapp_api.services.program_seed_data import EXERCISE_CATALOG, exercise_difficulty_level

# A deliberately small editorial allowlist. It prevents the public surface from
# turning the whole exercise catalogue into thin pages and excludes every
# user-created or personalized exercise by construction.
PUBLIC_EXERCISE_SLUGS = ("bench-press", "lat-pulldown", "squat")


@lru_cache(maxsize=1)
def public_exercises() -> tuple[dict[str, object], ...]:
    catalog = {
        slug: (title, primary_muscle, equipment)
        for slug, title, primary_muscle, equipment in EXERCISE_CATALOG
    }
    records: list[dict[str, object]] = []

    for slug in PUBLIC_EXERCISE_SLUGS:
        catalog_item = catalog.get(slug)
        profile_name = SLUG_TO_PROFILE.get(slug)
        if catalog_item is None or profile_name is None:
            raise RuntimeError(f"Published exercise {slug!r} is missing canonical domain data")
        title, primary_muscle, equipment = catalog_item
        profile = PROFILES[profile_name]
        records.append(
            {
                "slug": slug,
                "title": title,
                "primary_muscle": primary_muscle,
                "secondary_muscles": list(profile["secondary"]),
                "equipment": equipment,
                "difficulty_level": exercise_difficulty_level(slug),
                "technique_steps": list(profile["steps"]),
                "breathing": profile["breathing"],
                "common_mistakes": list(profile["mistakes"]),
                "safety_notes": list(DEFAULT_SAFETY_NOTES),
                "source_name": SOURCE_NAME,
                "source_url": SOURCE_URL,
                "source_license": SOURCE_LICENSE,
                "source_license_url": SOURCE_LICENSE_URL,
            }
        )
    return tuple(records)


def public_exercise(slug: str) -> dict[str, object] | None:
    return next((item for item in public_exercises() if item["slug"] == slug), None)
