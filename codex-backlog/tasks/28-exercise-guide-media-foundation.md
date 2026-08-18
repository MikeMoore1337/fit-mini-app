# TASK 28. Бесплатная media strategy для демонстрации упражнений

- Фаза: **Exercise media**
- Приоритет: **28/93**
- Зависит от: `23`
- Рекомендуемый reasoning: **High**
- Рекомендуемые skills: `$frontend-engineer`, `$backend-engineer`, `$qa-engineer`, `$product-designer`

## Цель

Исследовать и внедрить бесплатную lightweight media architecture для техники упражнений, переиспользуя current legal assets и обеспечивая Web/mobile/TMA.

## In scope

Инвентаризировать current start/active images, generated cardio assets, source/license, sizes/dimensions, missing exercises и static serving/cache. Никаких Fitness Online assets.

На representative exercises сравнить: 2-3 static phases, animated WebP (если уместно), short WebM и иной реально поддерживаемый lightweight browser-native вариант. Критерии: size/decode/load/clarity/accessibility/Web/iOS Safari/Android/TMA WebView/fallback/reduced motion.

Выбрать один default pattern + static fallback/poster/aspect ratio/loading policy. Не поддерживать пять formats ради эксперимента.

MVP без mandatory paid CDN/video/API. Использовать existing static/object storage conventions; если assets в repo — контролировать binary size.

Media metadata интегрировать с task `23`: type/url/poster/phase/alt/source/license/sort order. Animation/video без autoplay sound, respects reduced motion, text technique всегда остаётся.

Performance: lazy load, reserved dimensions, cache headers, не скачивать animation/video до открытия guide. Сделать pilot/pipeline на representative set, не обязательно наполнить весь catalog.

## Out of scope

Не покупать hosting/CDN, не копировать Fitness Online media/text, не делать remote API dependency или массовые сомнительные AI videos.

## Проверки

Representative Web/iOS/Android/TMA, static fallback, reduced motion, lazy load, 404 asset, source/license, CLS/cache/build size.

## Done when

Есть один выбранный lightweight media pattern с fallback, legal source metadata и reusable pipeline без paid dependency.

## Рекомендуемый commit

`feat(exercises): add lightweight guide media foundation`

## Процесс и отчёт

Следовать `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`.

Перед реализацией ещё раз проверить актуальный код, migrations, schemas, services, frontend и docs по текущему scope. Если функция уже реализована сильнее, чем предполагает task, не дублировать её: расширить существующую архитектуру или явно зафиксировать, что пункт уже закрыт.

Работать только в текущей feature-ветке. Не создавать/переключать ветки, не merge/rebase и не deploy в production. Не переходить к следующему task.

После изменений: профильные проверки по `AGENTS.md`, `git diff`, один логический commit при tracked changes.

В финальном отчёте: что уже существовало и было переиспользовано, изменения, ключевые файлы, migrations, formulas/permissions/content-source decisions, реально запущенные проверки, ограничения и commit hash.
