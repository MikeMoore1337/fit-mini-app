# Auth integration notes - release v7

Auth foundation уже реализована tasks `10-13`:

- `10` auth audit;
- `11` identity/session/linking hardening;
- `12` provider production readiness;
- `13` premium `/login`.

Brand task `07` остаётся visual source of truth для logo/favicon. `/login` не создаёт собственный wordmark.

## Current downstream positions

- Profile/account: completed `47`.
- Coach workspace: completed `48`.
- Core product improvements: `50-67`.
- Simplified Demo: `68-69`.
- Direct Trainer activation: `70`.
- Minimal Root Admin: `71`.
- Telegram Mini App platform hardening: `72`.
- Landing/Login final visual parity: `73`.
- Responsive/accessibility/states: `74`.
- Performance/motion: `75`.
- Skill-aware retrospective audit: `76`.
- Real-user validation: `77`.
- Production readiness: `78`.
- Final release gate: `79`.

## Invariants

- One internal account can link multiple verified identities.
- Valid TMA `initData` launch does not show browser `/login`.
- Direct Trainer activation does not change authentication or create a second account.
- Root authority is server-configured and cannot be obtained through linking.
- Demo continuation uses existing canonical auth/deep-link flow and never imports fixtures.
- Landing task `73` owns final public/auth visual parity while preserving security, provider availability and canonical brand assets.
- Post-release AI, translation and import work must reuse this auth foundation rather than add parallel identity systems.
