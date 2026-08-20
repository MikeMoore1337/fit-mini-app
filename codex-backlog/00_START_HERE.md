# Your Fitness Coach - FINAL pre-release backlog

Это замороженный backlog до первого релиза живым пользователям.

## Уже выполнено
Tasks `00-46` и integration gate `46A-46J`, включая `46C.1-46C.6`, считаются выполненными и не
запускаются повторно. Approved Design V2 внедрён на завершённых surfaces, а будущий backlog
синхронизирован с ним.

## Выбор модели Codex

Перед каждой новой Codex-сессией вручную выбрать модель по `MODEL_SELECTION.md`. Backlog не переключает runtime-модель автоматически.

## Следующая задача
`47-profile-account-experience.md`

Не переходить к task `48` в той же сессии.

## Финальная структура

```text
00-46  ✅ COMPLETED
46A-46J, включая 46C.1-46C.6  ✅ COMPLETED
47-57  Remaining core + advanced UX

58     Deterministic progression guidance
59     Notifications / reminders
59A    Main Telegram bot support / feedback
60     Account export + lifecycle
61     Cardio logging gap audit + minimal implementation

62-68  Demo Mode
69 -> 69A -> 70 -> 70A -> 71 -> 71A  Admin + trainer application activation
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

## Design V2 source of truth

- integration contract: `DESIGN_V2_INTEGRATION_NOTES.md`;
- approved specifications: релевантные `../docs/design/*v2*`;
- approved renders: `../docs/design/references/design-v2/`;
- implementation source: фактические shared Design V2 tokens/components;
- Landing implementation task: `tasks/73-landing-premium-refresh.md`.

`references/landing/landing-reference-dark.png`, `landing-reference-light.png` и
`LANDING_REFERENCE_NOTES.md` являются только historical context и не участвуют в visual acceptance.
Product truth, SEO, accessibility, security и privacy requirements имеют высший приоритет.


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
