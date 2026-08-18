# TASK 07. Канонический логотип и читаемый favicon

- Фаза: **Brand / Design System Foundation**
- Приоритет: **07/93**
- Зависит от: `01`, `05`, `06`
- Рекомендуемый reasoning: **High**
- Рекомендуемая модель: **GPT-5.6 Terra High**
- Рекомендуемые skills: `$product-designer`, `$frontend-engineer`, `$qa-engineer`

## Цель

До дальнейшей работы с темами, авторизацией, AppShell, Telegram Mini App и Landing зафиксировать один production-ready набор брендовых assets на основе утверждённого пользовательского референса.

Источник истины:

`codex-backlog/references/brand/your-fitness-coach-logo-reference-light-dark.png`

Также прочитать `codex-backlog/BRAND_ASSET_NOTES.md`.

Референс не нужно переосмыслять или редизайнить. Нужно аккуратно перенести утверждённую визуальную идею в чистые production SVG и favicon.

## Перед началом

Проверить текущий frontend/public asset pipeline и найти все существующие:

- logo/brand assets;
- favicon/icon/manifest assets;
- `<link rel="icon">`, Apple touch icon и web manifest, если они есть;
- места использования логотипа на Landing, auth shell, AppShell и Telegram surface;
- semantic brand/accent tokens из task `05`;
- существующие build/static asset conventions.

Если в проекте уже есть часть подходящей инфраструктуры, переиспользовать её. Не создавать параллельную систему assets.

## 1. Полный логотип

Создать чистый векторный production logo на основе референса:

- прозрачный фон;
- знак + надпись `YOUR FITNESS COACH`;
- отдельный вариант для светлой темы;
- отдельный вариант для тёмной темы;
- геометрия, композиция и характер знака соответствуют референсу;
- лаймовый акцент сохраняется;
- в светлой теме нейтральные элементы остаются тёмными;
- в тёмной теме нейтральные элементы остаются светлыми;
- никаких растровых изображений, embedded base64 PNG/JPEG или внешних шрифтов внутри SVG;
- никаких фоновых прямоугольников, glow/halo из исходного PNG или лишних декоративных эффектов.

Не использовать растровый reference-файл как production logo и не делать SVG-обёртку вокруг PNG.

Если точный шрифт референса не известен, не подключать новый font package только ради logo. Предпочтительно зафиксировать wordmark геометрически/path-ами или использовать уже утверждённый проектный шрифт только если результат визуально соответствует референсу.

## 2. Favicon - только знак

Сделать отдельный favicon на основе центрального знака.

Обязательные требования:

- без текста `YOUR FITNESS COACH`;
- не сжимать полный горизонтальный logo в favicon;
- знак должен быть узнаваем на 16x16 и хорошо читаться на 32x32;
- сохранить основную идею `Y` / `C` / штанги;
- разрешено слегка увеличить зазоры, упростить слишком тонкие/мелкие элементы и скорректировать optical weight именно для маленького размера;
- не превращать favicon в другой логотип;
- прозрачный фон, если это не ухудшает читаемость;
- favicon не должен сливаться ни со светлым, ни с тёмным browser chrome/tab background.

Canonical source - SVG.

Дополнительные `.ico`/PNG/Apple touch/PWA размеры создавать только если они реально нужны текущему стеку, существующему manifest или browser compatibility проекта. Производные файлы должны генерироваться из canonical vector source, а не рисоваться независимо.

Если динамический light/dark favicon надёжно поддерживается текущей архитектурой без hacks, можно использовать theme-aware SVG или корректные отдельные variants. Если нет - выбрать один high-contrast mark, который одинаково хорошо работает в обоих режимах.

## 3. Интеграция assets

Подключить canonical assets в тех местах, где бренд уже отображается сейчас, без массового redesign:

- public/Landing shell;
- существующий auth entry/shell, если он уже существует;
- существующий AppShell/header, если там предусмотрен logo;
- browser favicon metadata;
- web manifest/PWA metadata только если оно уже используется.

Не ждать task `73`, чтобы favicon появился в документе: базовая browser integration входит в этот task.

При этом не делать полноценный Landing redesign, auth redesign, AppShell redesign или Telegram polish - они остаются downstream tasks.

## 4. Контракт для downstream tasks

После этого task downstream код не должен создавать собственные варианты логотипа.

Зафиксировать понятный API/структуру assets, например через существующий Logo component или минимальный shared component, если это соответствует текущей архитектуре.

Нужно поддержать как минимум:

```text
full logo / light surface
full logo / dark surface
mark only / small icon
```

Task `08` должен использовать эти canonical logo variants при переключении темы, а не дублировать SVG.

Tasks `13`, `38`, `72`, `73`, `74`, `75` должны переиспользовать тот же brand source of truth там, где logo отображается.

## 5. Доступность и семантика

- Значимый полный logo получает корректное accessible name `Your Fitness Coach`.
- Декоративный повторяющийся logo должен быть скрыт от screen reader по существующим паттернам проекта.
- Favicon не требует отдельного accessible text.
- Нельзя использовать logo как замену текстовому H1 на Landing.

## 6. Визуальная проверка

Обязательно проверить фактический render, а не только наличие файлов.

Минимально:

- light и dark surfaces;
- desktop и mobile public shell;
- logo на 100%, 75% и типичных responsive размерах без размытия/обрезания;
- favicon визуально в 16x16 и 32x32;
- отсутствие белого/тёмного raster background вокруг SVG;
- отсутствие layout shift из-за неизвестных logo dimensions;
- отсутствие заметно отличающихся legacy logo в основных entry surfaces.

Скриншоты/временные сравнения хранить только в `.artifacts/brand/`.

## Out of scope

- не придумывать новый logo;
- не менять название продукта;
- не делать новый общий visual redesign;
- не менять всю palette приложения только ради logo;
- не перерисовывать Landing;
- не менять auth protocols;
- не добавлять тяжёлую graphics/icon dependency;
- не добавлять animated logo;
- не создавать merch/social media brand kit.

## Проверки

Запустить только релевантные проверки по текущему стеку:

- component/unit tests для Logo wrapper, если он появляется;
- typecheck/lint/format;
- production build;
- targeted browser smoke для public shell/favicon;
- ручная/visual проверка SVG на light/dark и favicon 16x16/32x32.

Проверить, что SVG не содержит embedded raster/base64 data и внешних font/network dependencies.

## Done when

- reference PNG сохранён только как design reference;
- есть canonical transparent SVG logo для light и dark surfaces;
- есть отдельный mark-only favicon без надписи;
- favicon читается на 16x16 и 32x32;
- favicon подключён к browser metadata;
- текущие основные brand entry points используют canonical assets или готовы к downstream integration без дублирования;
- downstream tasks имеют один source of truth по logo;
- проект собирается без новых тяжёлых зависимостей.

## Рекомендуемый commit

`feat(brand): establish canonical logo and favicon assets`

## Процесс и отчёт

Следовать `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`. Не переходить к следующему task. После изменений запустить только профильные проверки, проверить diff и создать один логический commit. В финальном отчёте перечислить созданные SVG/favicon assets, места интеграции, реально запущенные проверки, ограничения и commit hash.
