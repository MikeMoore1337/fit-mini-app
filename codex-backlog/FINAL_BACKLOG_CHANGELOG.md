# Final pre-release backlog changelog

Based on the previous final backlog.

## Preserved
- tasks 00-06 remain completed and are not renumbered;
- theme contract;
- SEO/public IA;
- auth;
- food platform;
- training domain;
- data confidence;
- adaptive calories;
- weekly check-ins;
- workout adaptation;
- offline active workout;
- program revisions/blocks;
- Demo/Admin/TMA/Landing;
- AI Coach last;
- no photo/image analysis.

## Brand revision
- added new task `07-brand-logo-favicon-foundation.md`;
- bundled the approved light/dark logo reference under `references/brand/`;
- production full logo must be transparent SVG for light and dark surfaces;
- favicon must use only the mark, without `YOUR FITNESS COACH`, and be optically readable at 16x16/32x32;
- downstream theme/auth/AppShell/TMA/Landing tasks must reuse one canonical brand source;
- former tasks `07-92` were shifted to `08-93`; their feature scope is otherwise preserved.

## Landing reference revision
- bundled approved light and dark Landing references under `references/landing/`;
- added `LANDING_REFERENCE_NOTES.md` as the visual interpretation contract;
- task `73` now follows the approved hero/capabilities/product showcase/client-trainer/demo/platform/FAQ/footer composition;
- reference PNGs are explicitly visual-only: fake testimonials, prices, trial terms, contacts and AI claims must not be copied unless factual;
- Landing must reuse the canonical logo from task `07`;
- task `73` is now recommended for **GPT-5.6 Sol High** because the visual target and implementation boundaries are explicit;
- final regression checks reference adherence without requiring pixel-perfect copying.

## Added before release from previous final revision
- progressive ordinary-user onboarding;
- deterministic load progression guidance;
- unified notification/reminder orchestration;
- account data export + deletion lifecycle;
- guarded manual cardio gap audit/minimal implementation;
- production operational readiness.

## Release policy
Task `93` ends feature development for the first release.
Further feature work is driven by real users and product analytics.

## Plain-language UX
The release-wide plain-language contract remains in force:
- beginner-friendly Russian by default;
- `RIR` primarily shown as `Повторы в запасе`;
- advanced workout concepts use progressive disclosure;
- analytics explains facts instead of internal jargon;
- AI Coach adapts terminology to the user's language;
- final release audit includes a novice terminology test.


## AI provider revision - 2026-08-17
- tasks `77-81` and `89` updated after review of newer free-API options;
- default production chain is now Cloudflare Workers AI -> OrcaRouter -> OpenRouter Free;
- task `80` changed from Pollinations.ai to OrcaRouter Free;
- `AI_FREE_ONLY` now distinguishes recurring free allocation from trial/promotional credits;
- provider metadata now includes data-handling policy needed for privacy-aware routing;
- requests are classified as `generic` or `personalized`, with authenticated Coach traffic failing closed when classification/policy is uncertain;
- Router cannot downgrade sensitivity just to obtain a response;
- NaraRouter and Pollinations.ai are deferred experimental candidates, not mandatory production adapters;
- telemetry records routing/free-tier/policy decisions without copying raw prompts, answers or tool payloads;
- supporting AI rules, source coverage, downstream smoke-test references and manifest were synchronized.
## Unified Web/TMA design revision - 2026-08-18
- Web, Mobile Web and Telegram Mini App now share one YFC visual system instead of intentionally different platform palettes;
- shared YFC Light/YFC Dark semantic tokens are canonical on both Web and TMA;
- Telegram `colorScheme` selects YFC Light/Dark, while `themeParams` no longer define feature-component colors;
- task `08` was simplified/reframed around one theme system and moved to Sol High because it migrates cross-platform state/runtime behavior;
- task `72` is now platform integration/hardening rather than a Telegram visual redesign;
- Mobile Web/TMA visual parity is explicitly checked in tasks `38`, `72`, `74` and `93`;
- task `75` guards against duplicated platform-specific UI bundles/assets;
- completed task `05` remains completed; its old Telegram color-mapping assumption is explicitly superseded by task `08`;
- `MODEL_SELECTION.md` now reflects the quality-first split: Terra High only for 26 bounded tasks, Sol High for all others, including `08`, `61`, `72`, `73`, `74`;
- `MODEL_SELECTION.md` and `CODEX_PROMPT_TEMPLATE.md` state that model selection is manual and is not triggered by text inside a task file;
- stale checklist reference to Pollinations task `80` was corrected to OrcaRouter.
