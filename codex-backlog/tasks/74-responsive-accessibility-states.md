# TASK 74. Cross-product responsive, accessibility и states hardening

- Фаза: **Cross-product hardening**
- Приоритет: **74/93**
- Зависит от: `13`, `14`, `45`, `46`, `49`, `50`, `58`, `59`, `60`, `61`, `68`, `71`, `72`, `73`
- Рекомендуемый reasoning: **High**
- Рекомендуемые skills: `$ui-audit`, `$frontend-engineer`, `$qa-engineer`

## Цель

После всех экранов провести единый cross-product проход, чтобы локально хороший UI не расходился по breakpoints, focus, forms и async states.

## In scope

Audit фактической Approved Design V2 implementation + исправление подтверждённых P0-P2 для landing, auth app, Today, workout, Nutrition, Progress, Programs/Exercises, Profile, Coach, Admin Workspace, AI, Demo Mode, public SEO/content pages, Telegram adapter. Перед проверкой прочитать `codex-backlog/DESIGN_V2_INTEGRATION_NOTES.md` и релевантные `docs/design/*v2*`:
- responsive/touch/keyboard/focus/contrast;
- labels/errors/aria-current/headings/landmarks;
- icon buttons, modals/drawers/focus trap/Escape;
- loading/empty/error/disabled/retry/partial;
- long text/wrapping;
- safe areas;
- reduced motion.

Viewports 1440/1280/768/390/360. Отдельно проверить canonical logo из task `07` на public/auth/AppShell surfaces: без обрезания, потери контраста и нечитабельного уменьшения. Отдельно проверить demo banner, contextual dialogs/sheets, reset и auth handoff states. Для Telegram не вводить отдельные dynamic product colors: `colorScheme` выбирает shared YFC Light/Dark, а platform-specific изменения ограничены shell/safe-area/runtime behavior. На 390/360 отдельно сравнить representative Mobile Web и TMA и устранить необоснованные visual divergences. Не показывать raw technical errors и не терять recoverable form data.

## Out of scope

Не придумывать новый visual direction, не делать второй redesign, не исправлять P3 ценой большого refactor, не добавлять dependency ради отчёта.



## Design V2 regression

Для public Landing использовать утверждённые `docs/design/references/design-v2/landing-*.png`, а для product surfaces — релевантные Design V2 renders и фактическую shared implementation. Не упрощать mobile layout так, чтобы терялись hierarchy, CTA или связь с real-product visuals. Legacy `codex-backlog/references/landing/landing-reference-*.png` не участвуют в acceptance. Не менять канонический visual language под видом accessibility fix без отдельного owner checkpoint.

## Проверки

После fixes повторить browser UI audit в light/dark на 1440/1280/768/390/360 и representative Mobile Web/TMA states. Tests/typecheck/lint/format/build/targeted e2e. Screenshots в `.artifacts/ui-redesign/a11y-responsive/`.

## Done when

Нет известных P0/P1 в проверенных flows; P2 исправлены/обоснованы; keyboard/touch/safe-area/reduced-motion работают; Mobile Web/TMA сохраняют одну YFC palette/components/visual hierarchy, а различия документированы как platform behavior.

## Рекомендуемый commit

`fix(ui): harden responsive and accessible interactions`

## Процесс и отчёт

Следовать `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`. Работать в текущей feature-ветке, не merge/deploy. Не переходить к следующему task. После изменений запустить только профильные проверки, проверить diff и создать один логический commit. В финальном отчёте перечислить изменения, ключевые файлы, миграции, реально запущенные проверки, ограничения и commit hash.


## Auth surface

Отдельно проверить premium auth/login surfaces на 1440/1280/768/390/360, keyboard/focus/error announcements/reduced-motion.

## New training surfaces
Отдельно проверить wizard, RIR/help, exercise media/lightbox, muscles/equipment/alternatives, trainer comments, knowledge/exercise public pages и contextual knowledge UI.

## Final release integration: added flows

Responsive/a11y coverage включает:
onboarding, progression rationale, notification preferences,
data export/delete confirmations и cardio logging.

## Plain-language usability acceptance

Accessibility includes terminology/cognitive usability.

Verify:
- unexplained abbreviations are not required for core flows;
- contextual help is accessible;
- narrow screens do not force cryptic abbreviations;
- default workout path stays simple.
