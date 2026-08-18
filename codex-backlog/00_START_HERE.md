# Your Fitness Coach - FINAL pre-release backlog

Это замороженный backlog до первого релиза живым пользователям.

## Уже выполнено
Tasks `00-06` считаются выполненными и не запускаются повторно.

## Выбор модели Codex

Перед каждой новой Codex-сессией вручную выбрать модель по `MODEL_SELECTION.md`. Backlog не переключает runtime-модель автоматически.

## Следующая задача
`07-brand-logo-favicon-foundation.md`

Она фиксирует утверждённый logo reference как canonical production SVG assets и отдельный читаемый favicon без надписи.

## Финальная структура

```text
00-06  ✅ COMPLETED
07     Brand logo + favicon foundation
08     Unified YFC theme / Web + TMA sync
09     Organic Growth
10-13  Auth
14     Progressive onboarding

15-22  Food platform
23-28  Training domain

29-40  Advanced deterministic foundations
41-54  Core UX / Trainer / Knowledge
55-57  Advanced UX / product analytics

58     Deterministic progression guidance
59     Notifications / reminders
60     Account export + lifecycle
61     Cardio logging gap audit + minimal implementation

62-68  Demo Mode
69-71  Admin
72     Telegram Mini App platform integration / hardening
73     Landing
74     Responsive / Accessibility
75     Performance

76-91  AI Coach - last feature block

92     Production operational readiness
93     Final release candidate audit
```

## Brand source of truth

- reference: `references/brand/your-fitness-coach-logo-reference-light-dark.png`;
- rules: `BRAND_ASSET_NOTES.md`;
- implementation task: `tasks/07-brand-logo-favicon-foundation.md`.

Downstream tasks must reuse the canonical logo assets from task `07`, not create their own variants.

## Landing visual source of truth

- dark reference: `references/landing/landing-reference-dark.png`;
- light reference: `references/landing/landing-reference-light.png`;
- interpretation rules: `LANDING_REFERENCE_NOTES.md`;
- implementation task: `tasks/73-landing-premium-refresh.md`.

The PNG references define composition and visual direction, not factual claims. Product truth, SEO, security and privacy requirements take precedence over text/data visible inside the reference images.


## Единый Web/TMA дизайн

Release contract: один YFC visual system для Web, Mobile Web и Telegram Mini App. Web/TMA используют одинаковые YFC Light/Dark palettes и shared components. Telegram отличается только platform integration (auth/initData, safe areas, viewport/keyboard, BackButton, haptics, deep links и shell behavior). Source of truth: `GLOBAL_RULES.md`, task `08` и task `72`.

## Freeze
После `93` новые фичи до релиза не добавляются.
Только release blockers, security/privacy, data-loss, broken core flow и severe regressions.

Дальнейшее развитие - по данным и обратной связи живых пользователей.

## Language / beginner UX

Release-wide rule: default UI must be understandable to a beginner.

See `PLAIN_LANGUAGE_UX.md`.

Technical terms may remain in code, but cannot be required knowledge for core flows.
