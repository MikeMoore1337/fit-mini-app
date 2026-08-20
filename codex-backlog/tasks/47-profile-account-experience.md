# TASK 47. Профиль, настройки и account-сценарии

- Фаза: **Core UX**
- Приоритет: **47/93**
- Зависит от: `05`, `13`, `38`
- Рекомендуемый reasoning: **Medium**
- Рекомендуемые skills: `$product-designer`, `$frontend-engineer`

## Цель

Отделить Profile/Account от ежедневного Nutrition flow и собрать спокойный, понятный settings experience.

## In scope

Сгруппировать: личные данные; фитнес-параметры/цели; trainer/Telegram links и invites; notifications; privacy/security; entry point/status shell будущей trainer application; опасные account actions.

Forms: правильные mobile keyboards, validation near field, loading/disabled, сохранение input при recoverable error; sticky save только если реально помогает. Account deletion/destructive actions визуально отделены. Multi-provider auth architecture из tasks `09-12` не переписывается. Сохранить provider/linking states из task `13`; trainer invite/privacy semantics не менять.

## Trainer application boundary

Task `47` отвечает только за понятное место раздела `Для тренеров` внутри Profile и сохранение существующего корректного состояния, если backend уже есть. Не создавать новую application schema, approve/reject API, capability mutation или Admin review по предположениям. Полный канонический flow реализуется в tasks `69A`, `70A`, `71A`. До них нельзя показывать ложное успешное отправление заявки.

## Design V2 contract

Перед UI-работой прочитать `codex-backlog/DESIGN_V2_INTEGRATION_NOTES.md` и релевантные `docs/design/*v2*`. Profile/Account собирается из существующих Design V2 form, button, panel, navigation и feedback primitives; не создавать локальные palette, typography, radii или settings-card system. Существенные изменения проверить в реальном браузере в light/dark на desktop и mobile; изменение канонического visual language требует отдельного owner checkpoint.

## Out of scope

Не менять authentication architecture из tasks `09-12`, trainer invite logic, privacy model или KBJU formulas; не добавлять health integrations. Не реализовывать professional verification, документы или verified trainer badge.



## Проверки

Incomplete/complete profile, parameter edit, Telegram link, coach invite, notifications empty/populated, privacy/destructive actions, validation. Playwright 1440/768/390/360 + related tests.

## Done when

Profile разделён на ясные группы, редкие/опасные действия не конкурируют с основными, бизнес-логика auth/privacy сохранена.

## Рекомендуемый commit

`feat(ui): refine profile and account experience`

## Процесс и отчёт

Следовать `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`. Не переходить к следующему task. После изменений запустить только профильные проверки, проверить diff и создать один логический commit. В финальном отчёте перечислить изменения, ключевые файлы, миграции, реально запущенные проверки, ограничения и commit hash.

## Program recommendation profile fields
Переиспользовать canonical goal/level/workouts-per-week. Equipment preference хранить в profile только если task `25` выбрал account-level storage; не создавать duplicate settings.

## Final release integration: release analytics

После tasks `58` и `61` Progress может показывать:
- exercise progression guidance/history context;
- cardio frequency/duration отдельно от strength metrics;
без смешивания разных единиц нагрузки.
