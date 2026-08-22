# Landing - Approved Design V2 implementation notes

Legacy files under `references/landing/` and `masters/premium-redesign-master.md` remain historical context only. They do not override:

1. factual product behavior and release scope;
2. security/privacy/auth/SEO/accessibility requirements;
3. `DESIGN_V2_INTEGRATION_NOTES.md` and current `docs/design/*v2*`;
4. shared Design V2 implementation;
5. canonical brand assets from task `07`;
6. implementation task `73`.

## Product message

The first-release hero communicates:

```text
тренировки + питание + прогресс + работа с тренером
в одном Web/TMA-продукте
```

AI, translation, import, news, progress photos, wearables and monetization are post-release and must not appear as available or `coming soon` features.

## Header

- canonical logo + wordmark;
- only real public routes/anchors;
- secondary Login action;
- one primary CTA;
- accessible compact mobile menu.

Do not invent Pricing, Reviews, Company or integration pages that do not exist.

## Hero

- strong, concise headline and supporting text;
- primary CTA + secondary Demo CTA;
- real product composition from current Web/Mobile UI;
- no fabricated dashboard, fake metrics or stock feature screenshots;
- no unverified counts, ratings, customers, testimonials or «free trial» claims.

## Capability strip

Maximum 5-6 high-signal real capabilities, for example:

- быстрый план и тренировка на сегодня;
- питание и цели КБЖУ;
- прогресс и замеры;
- работа с тренером;
- Web + Telegram Mini App.

Do not duplicate the full feature inventory.

## Product showcase

Prefer real representative flows:

1. Today/active workout;
2. nutrition diary/quick logging;
3. Progress;
4. trainer-client workspace.

Screens must be obtainable from the production product and match the selected light/dark theme.

## Self / Trainer audiences

Both are real audiences, but the promise remains focused:

- самостоятельный пользователь получает complete personal workflow;
- trainer replaces scattered spreadsheets and manual progress collection with program -> execution -> result -> correction;
- the landing must not imply built-in generic messenger, payments, marketplace, video calls or qualification verification.

Trainer mode is available directly, without application or beta gate.

## Demo

- Use only the curated safe scenarios from tasks `68-69`.
- State clearly that demo data is temporary.
- Do not promise migration of demo data into an account.
- Demo CTA remains secondary to opening/creating an account.

## Platforms

Explain one product on different surfaces:

- Web;
- Mobile Web;
- Telegram Mini App.

TMA is positioned for quick workout, nutrition and progress actions. Do not advertise a TMA article library.

## Social proof

Until verified evidence exists, hide testimonials/ratings or replace them with factual proof:

- supported platforms;
- real capabilities;
- transparent privacy/security facts;
- available demo;
- public methodology/materials.

Never invent names, photos, quotes, stars or user counts.

## FAQ

- crawlable and accessible;
- based on real objections and conditions;
- no claims about tariffs, subscriptions, unavailable integrations or deferred features;
- explain Web/TMA, trainer mode, data ownership, demo and core functionality factually.

## Footer

Only real product, legal, support and social links. Copyright year must be correct and not misleading.

## Responsive contract

Verify at minimum 1440, 1280, 1024, 768, 390 and 360 px.

On mobile:

- hero becomes a sequential flow;
- product visuals do not cover copy/CTA;
- capabilities become a readable grid;
- Self/Trainer section stacks vertically;
- FAQ/footer have no horizontal overflow.

## Acceptance source priority

```text
product truth/security/privacy/SEO/accessibility
-> Approved Design V2 docs/renders
-> shared implementation
-> canonical brand assets
-> task 73
```
