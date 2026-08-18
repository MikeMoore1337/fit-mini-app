# TASK 51. Weekly Check-in UX

- Фаза: **Core UX**
- Приоритет: **51/93**
- Зависит от: `34`, `43`, `48`
- Рекомендуемая модель: **GPT-5.6 Terra High**

## Цель

Сделать недельную сводку и feedback короткими, полезными и необязательными.

## In scope

- Entry из Today/Progress; objective confidence-aware summary; 2-4 optional subjective questions + note; skip/history; trainer view by permission; notification/deep-link; mobile/TMA.

## Out of scope

Без health questionnaire, AI conclusion и mandatory check-in.

## Проверки

Partial/full/empty week, skip/history, trainer revoke, mobile/a11y.

## Done when

Check-in занимает минуты и полезен без AI.

## Рекомендуемый commit

`feat(ui): add weekly check-in experience`

## Процесс

Следовать корневому `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`.

Все предыдущие tasks считаются выполненными. Текущий код, Git history и актуальный `docs/` — source of truth.
Не проводить повторный полный аудит репозитория, не перечитывать все task-файлы и весь `masters/`.
Если текущий task относится к одному master — читать только его. Использовать результаты предыдущих audit вместо повторного исследования.
Исследовать только релевантные файлы и подсистемы. Если функция уже существует — переиспользовать, не дублировать.
Крупное изменение вне scope не начинать автоматически: зафиксировать follow-up.

Работать только в текущей feature-ветке. Не create/switch branch, merge/rebase, deploy и не переходить к следующему task.
После реализации: только профильные checks, `git diff`, один логический commit при tracked changes, краткий отчёт с reused/changed/files/migrations-config/checks/follow-ups/hash.

## Final release integration: account settings

Tasks `59-60` используют Profile/Settings как единый вход для:
- notification preferences / quiet hours;
- export my data;
- unlink login method;
- delete account.

Не создавать отдельные несогласованные settings pages.
