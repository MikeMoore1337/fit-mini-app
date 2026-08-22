# Localization architecture checklist

## 1. Inventory

Map every current surface:

- public landing/product pages;
- authenticated client app;
- coach/admin;
- demo;
- AI Coach;
- Telegram Mini App;
- bot product messages/commands where in scope;
- backend validation/errors;
- notifications/email;
- knowledge/articles/exercises;
- generated PDF/report/export labels;
- analytics event display names, if user-facing;
- tests/snapshots/fixtures.

Classify each item as UI resource, domain label, editorial content, user-generated, technical literal or excluded.

## 2. Locale resolver specification

Record:

```text
supported locales
stored preference values
default/fallback
authenticated source
pre-auth source
Telegram/browser initial signals
manual override rule
sync/conflict rule
server request locale rule
background-job locale rule
```

Test resolver as a pure deterministic function where possible.

## 3. Resource structure

Check:

- stable type-safe keys;
- namespace ownership;
- interpolation variable types;
- plural/select forms;
- no sentence concatenation;
- no raw HTML translations;
- safe Markdown policy where needed;
- fallback chain;
- missing-key diagnostics;
- extraction/migration tooling;
- orphan-key detection;
- translator context/comments for ambiguous keys.

## 4. Domain data

For each catalogue/enum:

- stable id/code;
- RU/EN labels;
- aliases/search normalization;
- fallback label;
- custom/user-generated behavior;
- API representation;
- seed/migration/admin-edit strategy;
- export/import stability;
- unique constraints/indexes;
- no duplicate entity per language.

## 5. Formatting

Create wrapper APIs around project-standard `Intl`/CLDR functionality for:

- date;
- time;
- date-time;
- relative time;
- number;
- percent;
- unit;
- range;
- duration;
- timezone.

Avoid component-specific formatter options that produce inconsistent product output.

Verify Russian and English plural forms, decimals and unit ranges. Locale does not automatically change user unit preference.

## 6. Backend/API

- Stable error code separate from localized message.
- Request/effective locale propagated explicitly.
- No process-global mutable locale.
- Notifications use recipient locale.
- Async/background jobs restore locale deterministically.
- Audit/persistence stores stable codes, not translated labels.
- Generated report keeps requested locale and timezone.

## 7. Public Web/SEO

Record:

```text
default locale URL strategy
non-default locale prefix/domain strategy
canonical rule
hreflang mapping
x-default decision
sitemap generation
redirect behavior
indexability/review gate
localized metadata/structured data
internal link locale preservation
```

Do not emit reciprocal `hreflang` for incomplete/404/non-canonical pages.

## 8. Telegram

- TMA locale signal is initial only.
- Account preference shared with Web.
- Mini App adapter does not fork resources.
- Bot commands use valid Bot API language scopes only if approved.
- Russian-only channel remains excluded when required.
- Product notifications and editorial channel content are separate localization scopes.

## 9. Content workflow

Editorial translation requires:

- source locale/version;
- translator/reviewer;
- status;
- reviewed date;
- source links parity;
- no index before complete review;
- update propagation when source changes;
- locale-specific slug/redirect policy.

## 10. Migration rollout

Recommended sequence:

1. audit;
2. locale resolver/resources/formatters;
3. stable domain labels;
4. product UI;
5. public content/SEO;
6. TMA/bot product surfaces;
7. editorial/native-quality review;
8. final regression.

During mixed-version rollout, fallback must preserve current production language and behavior.

## 11. Reference standards

Re-check current sources:

- Unicode CLDR/LDML: https://unicode.org/reports/tr35/
- W3C Internationalization: https://www.w3.org/International/
- Search-engine internationalization guidance used by the project.

Use framework/library documentation for the exact APIs available in the repository version.
