# Localization regression matrix

## Resolver and persistence

- new anonymous visitor with Russian browser;
- new anonymous visitor with English browser;
- unsupported browser locale;
- Telegram RU/EN/unknown language code;
- user manually selects RU/EN;
- page reload;
- second tab;
- login after pre-auth choice;
- existing account preference conflicts with local preference;
- Web -> TMA and TMA -> Web;
- logout/shared device;
- offline/reconnect;
- account preference update failure;
- fallback resource missing.

Expected: manual authenticated preference wins according to documented policy, no loop or silent reset.

## Translation resources

- all required keys exist;
- interpolation placeholders match across locales;
- plural categories are valid;
- escaped text remains escaped;
- Markdown/HTML policy is safe;
- no raw key/internal enum in production;
- missing-key signal visible in test/development;
- no duplicate conflicting keys;
- no sentence built from grammar-sensitive fragments.

## Formats

Test representative values:

- zero/one/few/many/decimal;
- negative and large numbers;
- decimal/group separators;
- date around midnight;
- DST transition;
- date range;
- relative time;
- duration;
- kg/lb, cm/in, km/mi;
- kcal, grams, bpm;
- percentage;
- empty/unknown value.

## Domain data/search

- RU label returns canonical entity;
- EN label returns same id;
- alias in both languages;
- ambiguous alias;
- custom exercise remains user-entered;
- fallback label;
- import/export stable code;
- no duplicate seeded entity;
- admin edit preserves identity;
- search normalization for case, whitespace and `ё/е` policy.

## Product UI

For every critical flow in RU/EN:

- landing/login/onboarding;
- Today/dashboard;
- active workout;
- nutrition diary;
- progress/reports;
- programs/exercises;
- coach/admin;
- demo;
- AI Coach;
- account/export/delete;
- notifications/errors/empty/loading/recovery.

Visual states:

- 360/390/768/1440;
- light/dark;
- long names/content;
- keyboard open;
- modal/sheet;
- charts/table labels;
- screen reader names;
- focus order;
- no truncation hiding meaning.

## Public Web/SEO

- RU canonical routes unchanged;
- EN route exists only with complete content;
- status codes;
- `<html lang>`;
- title/description/OG;
- canonical;
- reciprocal hreflang;
- sitemap;
- robots/noindex for draft;
- structured data language/content parity;
- internal links keep locale;
- locale switch points to equivalent page or defined fallback;
- no mixed-locale breadcrumb/navigation.

## TMA and bot

- TMA valid launch RU/EN;
- manual switch without state loss;
- BackButton and platform controls;
- safe area/viewport;
- localized product notifications;
- command language scopes, if enabled;
- unknown locale fallback;
- no English news channel/post/digest regression.

## Backend and jobs

- API error code stable;
- localized validation message correct;
- background notification uses recipient locale;
- scheduled job after preference change follows policy;
- concurrent requests with different locales do not leak language;
- report generation locale/timezone;
- audit/event data stores stable code.

## Editorial review

- terminology glossary consistency;
- natural English/Russian;
- health/fitness claim meaning preserved;
- sources and limitations preserved;
- no accidental stronger promise in translation;
- author/reviewer/status/dates;
- native-quality review claim supported by actual process.

## Automated quality gates

Use what fits the repository:

- type checking of keys;
- missing/unused-key checks;
- placeholder parity;
- pseudo-localization/long-string mode;
- route/SEO assertions;
- component/e2e representative flows;
- visual/browser verification;
- mixed-language text scan with allowlist for technical literals.
