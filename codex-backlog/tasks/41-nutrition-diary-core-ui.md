# TASK 41. Nutrition - основной пищевой дневник UI

- Фаза: **Core UX**
- Приоритет: **41/93**
- Зависит от: `05`, `16`, `17`, `38`
- Рекомендуемый reasoning: **Medium**
- Рекомендуемые skills: `$product-designer`, `$frontend-engineer`

## Цель

Создать основной ежедневный Nutrition experience сразу на новой дизайн-системе, не делая промежуточный старый UI.

## In scope

Сделать раздел `Питание` с date navigation, breakfast/lunch/dinner/snacks, entries, mass/serving, per-entry macros, day totals, targets, remaining/deviation, quick add. Цель КБЖУ и calculator должны выглядеть частью одного Nutrition раздела, а не отдельным продуктом.

Для core add flow использовать локальные recent/favorites/own/system results из task 17. Поддержать add/edit/delete quantity, loading/empty/error/partial/retry/disabled. Небольшое превышение целей не подсвечивать агрессивно.

Mobile first, desktop richer composition, keyboard/focus/labels/touch targets. Не терять input при recoverable error.

## Out of scope

Не добавлять camera scan/recipes/copy advanced flows - task 42. Не менять KBJU formulas или food domain. Не подключать внешние API напрямую из frontend.



## Проверки

Component/API tests: display, date, add/edit/delete, local quick add, empty/error/reload persistence. Playwright 1440/768/390/360, keyboard/focus, no overflow.

## Done when

Пользователь может ежедневно вести питание быстро и понятно на Web/Mobile через общий код; core flow не зависит от внешнего provider.

## Рекомендуемый commit

`feat(ui): build premium nutrition diary experience`

## Процесс и отчёт

Следовать `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`. Не переходить к следующему task. После изменений запустить только профильные проверки, проверить diff и создать один логический commit. В финальном отчёте перечислить изменения, ключевые файлы, миграции, реально запущенные проверки, ограничения и commit hash.
