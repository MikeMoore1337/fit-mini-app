from typing import get_args

from fitminiapp_api.models.user import UserProfile
from fitminiapp_api.schemas.user import OnboardingField, OnboardingStateResponse, ProfileGoal

ONBOARDING_REQUIRED_PROFILE_FIELDS: tuple[OnboardingField, ...] = ("goal",)
CANONICAL_PROFILE_GOALS = frozenset(get_args(ProfileGoal))


def build_onboarding_state(profile: UserProfile | None) -> OnboardingStateResponse:
    """Derive first-run state from authoritative profile fields."""
    missing_fields = [
        field
        for field in ONBOARDING_REQUIRED_PROFILE_FIELDS
        if profile is None or getattr(profile, field) not in CANONICAL_PROFILE_GOALS
    ]
    return OnboardingStateResponse(
        status="required" if missing_fields else "complete",
        required_fields=list(ONBOARDING_REQUIRED_PROFILE_FIELDS),
        missing_fields=missing_fields,
    )
