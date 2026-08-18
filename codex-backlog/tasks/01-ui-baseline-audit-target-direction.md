# TASK 01. Baseline UX/UI audit и целевая арт-дирекция

- Статус: **COMPLETED — user-confirmed before backlog v3**

- Фаза: **Foundation**
- Приоритет: **01/93**
- Зависит от: `00`
- Рекомендуемый reasoning: **High**
- Рекомендуемые skills: `$ui-audit`, `$product-designer`

## Цель

Получить фактический visual/interaction baseline реальных экранов и зафиксировать минимальную целевую модель premium sport-tech до изменения дизайн-системы.

## In scope

Read-only аудит landing + authenticated app + active workout + progress + programs + exercises + nutrition + profile + coach + доступный Telegram-specific слой.

Обязательно проверить реальные render состояния через Playwright на 1440/1280/768/390/360, где применимо: populated/empty/loading/error/selected/hover/focus/disabled/modal/long text. Классифицировать P0-P3.

Оценить hierarchy, competing CTA, nested cards/borders, density, touch targets, navigation, desktop/mobile composition, typography, colors, Web/Telegram coherence, a11y, motion baseline, overflow/layout shifts, forms, lists/tables и active workout.

Зафиксировать 5-10 главных проблем, эталонные экраны и правила cards/borders/shadows/accent/motion. Разные цвета Web/Telegram сами по себе дефектом не считать.

## Out of scope

Не менять продуктовый код. Не исправлять дефекты по пути. Не придумывать новые продуктовые функции. Не коммитить audit report в `docs/`.



## Проверки

Screenshots/report хранить в `.artifacts/ui-redesign/baseline/`. Просмотреть все screenshots. Проверить отсутствие tracked changes.

## Done when

Есть P0-P3 findings, target visual language, карта IA и перечень системных проблем. Production-код не изменён. Commit не создаётся.

## Процесс и отчёт

Следовать `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`. Не переходить к следующему task. После изменений запустить только профильные проверки, проверить diff и создать один логический commit. В финальном отчёте перечислить изменения, ключевые файлы, миграции, реально запущенные проверки, ограничения и commit hash.
