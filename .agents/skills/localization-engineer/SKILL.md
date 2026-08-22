---
name: localization-engineer
description: >
  Design, implement or review internationalization and localization across UI, backend messages,
  domain dictionaries, formatting, public routes, SEO and Telegram Mini App. Use when adding or
  changing supported locales. Do not use for a one-off copy edit with no locale architecture impact.
---

# localization-engineer

Создавай несколько языковых вариантов одного продукта, а не несколько расходящихся приложений.

## Сначала

Перед изменением кода инвентаризируй:

- все user-facing Web/TMA/Admin/Coach/Demo/AI surfaces;
- hardcoded strings и locale-specific formatters;
- backend errors, notifications, email/bot templates;
- public metadata, `<html lang>`, canonical, sitemap и structured data;
- domain dictionaries, enums, statuses, exercises, equipment и goals;
- current profile/preferences/pre-auth storage;
- Telegram/browser locale signals;
- tests, snapshots и content source;
- существующие i18n libraries и generated types.

Классифицируй строки:

```text
UI resource | domain label | public editorial content | user-generated | technical literal | out of scope
```

Не меняй бизнес-логику, formulas, permissions или security под видом перевода.

## Locale contract

Зафиксируй поддерживаемые locale identifiers и preference contract, например:

```text
auto | ru | en
```

Отделяй:

- **stored preference** - что выбрал пользователь;
- **effective locale** - какой locale используется сейчас;
- **initial signal** - browser/Telegram language при первом входе.

Рекомендуемый приоритет:

1. authenticated account preference;
2. pre-auth local preference;
3. platform signal при первом запуске;
4. browser languages;
5. product fallback.

Manual choice всегда имеет приоритет и не должен перезаписываться очередным platform signal.

Сохраняй preference между Web/TMA и после auth handoff без потери другого состояния. Определи
конфликтную политику для нескольких вкладок/устройств и не создавай бесконечный sync loop.

## Translation resources

- Используй одну locale infrastructure и type-safe keys, если стек это поддерживает.
- Делай namespaces по устойчивым продуктовым областям, а не по случайным компонентам.
- Не используй raw English/Russian sentence как key.
- Не склеивай предложения из переводимых фрагментов: порядок слов и грамматика различаются.
- Используй interpolation и locale-aware plural/select rules.
- Сохраняй placeholders, markup и variables типизированными и проверяемыми.
- Не рендери недоверенный translation content через unsafe HTML.
- В development/test missing key должен быть заметен; production fallback должен быть безопасным и
  наблюдаемым, а не показывать internal enum/code.
- Удаляй orphan keys только после поиска динамических consumers и tests.

## Stable domain data

Business identifiers и enum codes остаются language-neutral.

Правильно:

```text
exercise_id=42
code="bench_press"
labels={ru: "Жим лёжа", en: "Bench press"}
```

Неправильно:

- создавать второе упражнение ради английского названия;
- использовать translated label как foreign key;
- менять stable API code при переключении языка;
- автоматически переводить custom/user-generated name.

Для catalog/search:

- разные языковые labels и aliases ведут к одной canonical entity;
- aliases имеют source/scope/ownership;
- matching/import не должен менять identity;
- API явно возвращает stable code/id и requested/fallback labels;
- exports/imports используют machine-stable fields.

## Formatting

Используй стандартные locale-aware formatter APIs и актуальные CLDR/Intl semantics вместо ручных
шаблонов.

Проверяй:

- cardinal/ordinal plural forms;
- decimal/group separators;
- date/time order;
- timezone и daylight-saving boundaries;
- relative time;
- units, ranges и abbreviations;
- percentages;
- currency, если применимо;
- first day of week и calendar assumptions, если они влияют на продукт.

Храни canonical machine value отдельно от presentation. Не переводить и не округлять данные в БД
ради UI.

Для fitness продукта отдельно проверь `кг/lb`, `км/mi`, `см/in`, `ккал`, `г`, `уд/мин`, duration и
range formatting. Unit preference и locale - разные настройки.

## Backend, API и notifications

- Возвращай stable machine-readable error codes и локализуй user-facing message на определённой
  границе.
- Не делай translated message единственным API contract.
- Server-generated notifications используют locale пользователя на момент формирования по
  зафиксированной policy.
- Background jobs не должны зависеть от process-global locale.
- Сохраняй locale/translation version там, где повторный render должен быть воспроизводимым.
- Не логируй полный private notification content без необходимости.

## Public routes и SEO

Для multilingual public surface:

- зафиксируй URL strategy до массового перевода;
- сохраняй стабильность default-language URLs;
- каждая indexable locale page имеет полный reviewed content;
- canonical указывает на canonical URL того же locale, если архитектура не задаёт другое обоснованное
  правило;
- reciprocal `hreflang` публикуется только для реально существующих эквивалентов;
- sitemap содержит только canonical/indexable/reviewed locale URLs;
- internal links по возможности сохраняют locale;
- title/description/OG/structured data соответствуют visible content;
- empty, partial или machine-draft page не индексируется;
- redirects рассматриваются как URL migration, а не как перевод строки.

Используй `$seo-auditor` для technical SEO и `$evidence-content-editor` для публичных материалов.

## Telegram Mini App и бот

- Telegram `language_code` - initial auto signal, не trusted identity и не вечный override.
- TMA использует тот же account preference и resources, что Web.
- Runtime language switch не должен терять форму, workout или navigation state без причины.
- `BackButton`, safe areas, theme и platform controls не требуют отдельного translation tree.
- Bot commands/menu/profile localization делай только в рамках текущей bot architecture и command
  scopes.
- Не создавай English channel/news pipeline, если project scope оставляет канал русскоязычным.

Используй также `$telegram-engineer`.

## User-generated content

Не переводи автоматически:

- имена;
- заметки;
- trainer comments;
- сообщения;
- custom exercises;
- uploaded program content.

Можно локализовать surrounding labels и предоставить явный пользовательский перевод как отдельную
функцию, если он когда-либо появится.

## Качество текста

Translation review проверяет не буквальное совпадение, а:

- естественность;
- терминологию продукта и домена;
- ясность для целевой аудитории;
- tone of voice;
- consistency;
- отсутствие двусмысленных health/fitness promises;
- длину и layout impact.

Не заявляй, что проведён native review, если его фактически не было. Зафиксируй, кто и как выполнил
review, либо честно укажи ограничение.

## UI и accessibility

Проверяй минимум:

- длинные строки и кнопки;
- narrow mobile/TMA widths;
- line wrapping и truncation;
- tables/charts/tooltips;
- form labels/errors/hints;
- keyboard/focus;
- screen-reader names;
- alt text;
- light/dark;
- locale switch accessibility;
- mixed-language states.

Не заменяй видимый label на tooltip-only перевод.

## Tests

Автоматизируй применимые проверки:

- locale resolver и manual override;
- pre-auth/auth persistence;
- fallback/missing key;
- interpolation/plurals;
- dates/numbers/units/timezones;
- stable domain identity и bilingual search;
- backend errors/notifications;
- public route/canonical/hreflang/sitemap;
- Web/TMA continuity;
- no raw enum/internal key;
- no mixed-language critical flow;
- pseudo-localization или controlled long-string mode;
- build/type/lint и focused e2e.

Для полной работы прочитай:

- `references/LOCALIZATION_ARCHITECTURE_CHECKLIST.md`;
- `references/LOCALIZATION_REGRESSION_MATRIX.md`.

## Не делай

- отдельный frontend tree на каждый язык;
- runtime machine translation как source of truth;
- автоматический перевод user-generated content;
- locale detection, которая каждый раз перезаписывает manual choice;
- translated database identifiers;
- indexable machine drafts;
- массовую замену строк без проверки context и grammar;
- фиктивный native review.

## Финальный отчёт

Укажи:

- locale contract и priority;
- resources/domain/public content, которые изменены;
- persistence и Web/TMA continuity;
- formatting и SEO decisions;
- review, реально выполненный для текста;
- tests и известные untranslated/out-of-scope surfaces.
