# Release scope freeze

## Decision
This is the final feature backlog for the first real-user release.

## Before release
Do not add new product features after task `93`.

Allowed work:
- security/privacy fixes;
- data-loss/corruption fixes;
- broken auth/onboarding/payment-like critical flow fixes (billing is not currently in scope);
- broken food/training/progress/trainer core flows;
- severe accessibility/performance regressions;
- operational release blockers.

Not a valid reason to expand pre-release scope:
- competitor has feature X;
- idea sounds useful;
- AI could also do Y;
- "nice to have";
- speculative optimization without user evidence.

## Explicitly deferred until after live users
- progress photos / photo comparison / AI image-body analysis;
- wearables, Apple/Google Health, Strava;
- social network/feed/friends/followers;
- trainer marketplace/ratings;
- generic messenger/video calls;
- Trainer Copilot;
- autonomous AI writes;
- AI-generated notification scheduling;
- complex recovery/readiness scores;
- advanced periodization engine;
- broad imports from competitors;
- billing/subscriptions until monetization is actually required.

## After release
Create a new backlog only from:
1. real user feedback;
2. product analytics;
3. observed support problems;
4. conversion/retention bottlenecks;
5. security/reliability needs.

## UX language is a release-quality requirement

Fixing confusing mandatory terminology is release-quality work, not feature expansion.
Do not use terminology cleanup as a reason to redesign unrelated screens or add features.
