# TASK 42. Nutrition - поиск, свои продукты, рецепты, копирование и barcode UX

- Фаза: **Core UX**
- Приоритет: **42/93**
- Зависит от: `18`, `19`, `20`, `41`
- Рекомендуемый reasoning: **Medium**
- Рекомендуемые skills: `$product-designer`, `$frontend-engineer`

## Цель

Добавить advanced Nutrition flows поверх уже рабочего дневника, сохранив быстрый mobile path.

## In scope

Реализовать UI для:
- local-first product search с debounce/min length/cancel stale requests;
- external provider как доп. источник с понятным fallback;
- create/edit own food;
- favorites/recent;
- recipes/dishes с итоговым весом и serving;
- repeat product/copy meal/copy day с явным source/target и защитой double submit;
- barcode manual input;
- camera scanning: сначала feature detection стандартного Barcode Detection API, лёгкая client fallback library только если действительно нужна; permission denied/no camera/unsupported/manual fallback.

Telegram не требует отдельного server scanning path. Не показывать raw 429/timeout/provider errors.

## Out of scope

Не менять food calculations/provider contracts, не добавлять платный barcode API, не вводить бытовые меры без надёжного веса.



## Проверки

Search ordering/stale requests, provider unavailable, own food validation, recipe math UI integration, copy confirmation/double submit, barcode local/external/not-found/manual, camera permission/unsupported where testable, mobile 390/360 and desktop smoke.

## Done when

Все advanced food flows доступны без поломки core diary; при недоступном external provider пользователь продолжает работать локально.

## Рекомендуемый commit

`feat(ui): add advanced nutrition discovery and reuse flows`

## Процесс и отчёт

Следовать `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`. Не переходить к следующему task. После изменений запустить только профильные проверки, проверить diff и создать один логический commit. В финальном отчёте перечислить изменения, ключевые файлы, миграции, реально запущенные проверки, ограничения и commit hash.

## Final release integration: first-run state

App shell должен корректно работать после task `14`:
- incomplete onboarding не создаёт redirect loop;
- returning complete user не видит onboarding повторно;
- optional feature setup не блокирует shell.
