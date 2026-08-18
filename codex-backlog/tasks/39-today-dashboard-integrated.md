# TASK 39. Интегрированный главный экран «Сегодня»

- Фаза: **Core UX**
- Приоритет: **39/93**
- Зависит от: `21`, `22`, `27`, `38`
- Рекомендуемый reasoning: **Medium/High**
- Рекомендуемые skills: `$product-designer`, `$frontend-engineer`

## Цель

Сделать один окончательный Today dashboard, объединяющий продуктовые требования Food Platform и premium redesign, чтобы не реализовывать экран дважды.

## In scope

Иерархия: context/day -> ближайшая/текущая тренировка -> главный CTA start/resume -> compact daily summary -> progress/high-signal data -> onboarding only if needed -> secondary actions.

Nutrition summary: eaten/target calories + P/F/C и быстрый entry в Nutrition, без копии полного дневника. Weight: last value + delta/trend при реальных данных. Adherence summary только если task 21 дал корректные metrics.

Если тренировки нет - ясное state. Duration/volume только из реальных данных. Onboarding после выполнения не доминирует. Один secondary API failure не должен обнулять dashboard. Не строить тяжёлый новый aggregator, если данные уже доступны безопасными сервисами.

## Out of scope

Не придумывать readiness/recovery/streak, не добавлять AI entry до AI UI task `90`, не переделывать active workout, не создавать фиктивные значения.



## Проверки

Сценарии: new user, incomplete profile, program/no history, workout today/started/completed/no workout, nutrition available/unavailable, partial API failure. Playwright 1440/768/390/360 + component/API contract checks.

## Done when

Пользователь за 1-2 секунды понимает, что делать сегодня; primary CTA очевиден; dashboard корректно деградирует при неполных данных.

## Рекомендуемый commit

`feat(ui): redesign integrated today dashboard`

## Процесс и отчёт

Следовать `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`. Не переходить к следующему task. После изменений запустить только профильные проверки, проверить diff и создать один логический commit. В финальном отчёте перечислить изменения, ключевые файлы, миграции, реально запущенные проверки, ограничения и commit hash.

## Training analytics restraint
Today может использовать только 1-2 high-signal values из task `27`; не переносить RIR/muscle charts на главный экран ради количества данных.
