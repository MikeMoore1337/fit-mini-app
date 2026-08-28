# Source coverage v11

## Product inputs covered

- User-confirmed completed implementation/design range `00-49B`.
- Current production source of truth: approved Design V2.
- Added requirement for a one-time rendered UI/component consistency audit before `49C` because completed work spans multiple generations of rules, roles and skills.
- Reuse/shared primitives, coherent sizes/tokens/states and visual correctness are required across current production UI.
- Personal/client-facing flows are smartphone-first; desktop remains required and Coach/Admin may retain justified desktop-first density.
- Landing, `/login`, authenticated Web, Mobile Web and existing TMA shared composition are included in the consistency baseline.
- Current `.agents` role/skill contracts and Mobile/TMA acceptance matrix.
- Existing factual product behavior, brand assets, SEO, accessibility, performance and security constraints.

## Decision safety

- Design V2 remains active until explicit owner decision and task `49G` closure.
- Task `49B1` may normalize only the current V2 implementation and cannot adopt visual alternatives A/B/C.
- New skills improve implementation quality but do not automatically invalidate approved design or expand feature scope.
- Product-wide audit is done once in `49B1`; future feature tasks preserve the baseline and inspect only their changed surface/shared usages.

## Explicit omissions

Post-release features remain outside release dependencies. See `RELEASE_SCOPE_FREEZE.md`.
