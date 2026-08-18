# TASK 18. Рецепты/блюда и копирование питания - backend

- Фаза: **Core data**
- Приоритет: **18/93**
- Зависит от: `16`, `17`
- Рекомендуемый reasoning: **Medium**

## Цель

Позволить переиспользовать типовое питание без повторного ручного ввода.

## In scope

Рецепт/блюдо собирается из продуктов и считает общий вес, общие КБЖУ, КБЖУ на 100 г и произвольную массу готового блюда. Изменение массы после готовки учитывать только при явно введённом итоговом весе - ничего не угадывать. User recipes приватны.

Поддержать повтор продукта, copy meal, copy day, повтор вчерашнего breakfast/lunch/dinner. API должен явно знать source date/meal и target date/meal. Защитить double-submit/случайное дублирование подходящим для архитектуры способом.

## Out of scope

Не делать внешний provider, camera scanner, dashboard/adherence и финальный UI.



## Проверки

Recipe math, cooked final weight, serving from recipe, copy product/meal/day, double-submit safety, ownership, timezone target date.

## Done when

Рецепты считаются детерминированно, копирование прозрачно и не создаёт скрытых дублей.

## Рекомендуемый commit

`feat(food): add recipes and meal copying`

## Процесс и отчёт

Следовать `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`. Не переходить к следующему task. После изменений запустить только профильные проверки, проверить diff и создать один логический commit. В финальном отчёте перечислить изменения, ключевые файлы, миграции, реально запущенные проверки, ограничения и commit hash.
