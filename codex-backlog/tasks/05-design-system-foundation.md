# TASK 05. Основа дизайн-системы и UI primitives

- Статус: **COMPLETED — user-confirmed before backlog v3**

- Фаза: **Foundation**
- Приоритет: **05/93**
- Зависит от: `01`
- Рекомендуемый reasoning: **High**
- Рекомендуемые skills: `$product-designer`, `$frontend-engineer`

## Цель

До массового редизайна создать устойчивые semantic tokens и переиспользуемые primitives, чтобы новые Food/AI/основные экраны сразу использовали одну систему.

> **Актуализация после выполнения:** task `05` уже завершён и не запускается повторно. Изначальная идея отдельного Telegram color mapping заменена release-контрактом task `08`: primitives/tokens сохраняются, но Web и TMA используют одну YFC Light/Dark palette; Telegram `colorScheme` только выбирает light/dark.

## In scope

Проверить текущие styles/shared UI/theme/Telegram mapping/landing tokens. Создать или упорядочить только реально переиспользуемые:
- typography/spacing/radius scales;
- semantic colors, surfaces, borders/elevation, content widths;
- focus/touch target/motion tokens;
- button/icon button; field/input/select; surface/card; section header; badge/status; metric; tabs/segmented controls; skeleton/loading; empty/error state.

Web и TMA используют общие semantic YFC tokens; актуальный runtime theme contract определяется task `08`. `prefers-reduced-motion` обязателен. Не делать всё bold, не давать тень каждой карточке, border использовать только для реальных уровней.

## Out of scope

Не редизайнить все экраны, не менять routes/backend, не подключать Tailwind/MUI/Ant/Chakra, не делать массовую миграцию legacy классов одним коммитом.



## Проверки

UI primitive tests где есть, typecheck, lint, format check, production build. Visual smoke нескольких light/dark экранов и shared Web/TMA theme behavior.

## Done when

Есть согласованные tokens/primitives, базовые states и reduced-motion support без тяжёлого UI framework; итоговый Web/TMA palette contract нормализуется task `08`.

## Рекомендуемый commit

`refactor(ui): establish premium design system foundation`

## Процесс и отчёт

Следовать `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`. Не переходить к следующему task. После изменений запустить только профильные проверки, проверить diff и создать один логический commit. В финальном отчёте перечислить изменения, ключевые файлы, миграции, реально запущенные проверки, ограничения и commit hash.
