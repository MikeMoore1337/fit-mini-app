# Recommended Codex model by task

Final pre-release quality-first policy.

`00-06` are completed and are not rerun.

Важно: этот файл является рекомендацией. Codex не переключает runtime-модель автоматически из текста backlog. Перед запуском отдельной Codex-сессии модель/reasoning нужно выбрать вручную.

## Default

**GPT-5.6 Sol High** - architecture, security, auth, domain rules, migrations, cross-system behavior, audits, release hardening and high-polish cross-cutting work.

**GPT-5.6 Terra High** - bounded implementation where architecture/contracts are already established.

## Terra High tasks

```text
07  brand-logo-favicon-foundation
16  food-diary-backend
17  food-product-library-search
18  recipes-copying-backend
20  barcode-lookup-backend
24  rir-workout-set-foundation
34  weekly-check-in-foundation
38  app-shell-navigation
39  today-dashboard-integrated
41  nutrition-diary-core-ui
42  nutrition-discovery-recipes-barcode-ui
43  progress-experience
44  programs-exercises-experience
45  program-selection-wizard-experience
46  exercise-guide-encyclopedia-experience
49  trainer-context-comments-experience
51  weekly-check-in-experience
52  adaptive-energy-calibration-experience
53  workout-adaptation-experience
54  program-history-and-training-blocks-experience
55  body-priorities-and-anthropometry-experience
56  data-confidence-product-integration
57  product-analytics-core-instrumentation
64  demo-fixtures-ephemeral-interactions
65  demo-ux-conversion
90  ai-ui-integration
```

## Sol High tasks

Все остальные незавершённые tasks, в том числе cross-cutting задачи:

```text
08  unified theme / Web + TMA sync
61  cardio gap audit + conditional implementation
72  Telegram Mini App platform integration/hardening
73  approved-reference Landing premium implementation
74  responsive/accessibility/states cross-product hardening
```

## Why these five are Sol High

- `08` - cross-platform theme state, persistence, runtime system/Telegram changes and migration from legacy platform color mapping.
- `61` - audit first, implementation path depends on findings.
- `72` - cross-product Telegram integration across auth/navigation/theme/safe-area/keyboard/deep-links/product flows.
- `73` - public commercial surface where visual judgment and polish matter.
- `74` - product-wide audit/fixes across responsive, accessibility and async states.

## New trainer application tasks

`69A`, `70A` and `71A` require **GPT-5.6 Sol High** because they combine migrations, state transitions, RBAC, concurrency, audit, notifications and cross-context UX.

## Retrospective remediation gate

`46C.6` requires **GPT-5.6 Sol High** because it preserves a security-sensitive production
network path across auth, configuration, deployment diagnostics and regression tests.

## Borderline tasks

Terra High can sometimes work for `40`, `47`, `48`, `71`, `75`, `80`, `83` when an implementation plan is already fixed and tests strongly guard behavior. Quality-first default remains **Sol High**.
