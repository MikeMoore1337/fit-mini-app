# TASK 93. Финальный интегрированный audit, regression и polish

- Фаза: **Final gate**
- Приоритет: **93/93**
- Зависит от: `07`, `13`, `14`, `22`, `23`, `24`, `25`, `26`, `27`, `28`, `29`, `30`, `31`, `32`, `33`, `34`, `35`, `36`, `37`, `38`, `39`, `40`, `41`, `42`, `43`, `44`, `45`, `46`, `47`, `48`, `49`, `50`, `51`, `52`, `53`, `54`, `55`, `56`, `57`, `58`, `59`, `60`, `61`, `62`, `63`, `64`, `65`, `66`, `67`, `68`, `69`, `70`, `71`, `72`, `73`, `74`, `75`, `76`, `77`, `78`, `79`, `80`, `81`, `82`, `83`, `84`, `85`, `86`, `87`, `88`, `89`, `90`, `91`, `92`
- Рекомендуемый reasoning: **High**
- Рекомендуемые skills: `$ui-audit`, `$qa-engineer`, `$code-reviewer`; `$product-designer` только для подтверждённых визуальных fixes

## Brand identity release gate

До общего regression gate проверить:

- light/dark full logo соответствует canonical assets task `07`;
- нигде в основных public/auth/app/TMA surfaces не осталось конфликтующего legacy logo;
- favicon не содержит wordmark, читается на 16x16/32x32 и корректно подключён;
- favicon/logo не имеют raster background, embedded base64 raster или внешних font dependencies;
- Landing и `/login` не создают собственную версию бренда.

## Цель

Независимо проверить весь итоговый продукт после Food Platform + Redesign + AI Coach + Demo Mode + полноценного trainer experience, исправить подтверждённые P0-P2 в согласованном scope и выдать финальный release-style отчёт.

## In scope

Audit: landing, auth, Today, active workout, Progress, Programs, Exercises, Nutrition core+advanced, Profile, Coach workspace, trainer onboarding/program workflow, AI, user+trainer Demo Mode, Admin shared primitives, Telegram adapter. P0-P3 severity. Исправить все P0/P1, P2 если не требует изменения согласованного behavior, дешёвые P3 по желанию. После fixes повторный audit.

Critical flows минимум:
- Web login -> Today -> workout -> complete set/workout -> Progress;
- Nutrition -> add/edit/copy/search/barcode fallback -> persistence;
- Programs -> open/edit available flow;
- Coach -> client list -> client -> program/history/progress/measurements/adherence/nutrition if permitted -> allowed action + denied чужой/former/revoked client;
- AI -> general/personal/app-help/out-of-scope + cross-user negative + free-provider failover/unavailable;
- Demo user -> enter -> explore/edit -> save interception -> reset -> auth/Telegram; Demo trainer -> synthetic client workspace -> client/program/history/progress -> temporary action -> auth; AI/side effects blocked;
- Telegram-like launch -> Today -> workout/nutrition/AI -> nested back.

Code review: dead/duplicate CSS/tokens, debug logs, TODO/test-only production code, inaccessible handlers, unsafe HTML, unnecessary deps.

Backend полный suite не запускать без причины; targeted Food/AI/security/API checks - если затронуты или нужны для critical flow. Docs обновлять только если архитектура/поведение документировано и изменилось.


## Trainer release gate

Проверить trainer experience как полноценный коммерческий workflow, а не вторичную admin-role. Обязательный critical flow:

```text
Landing / authenticated entry
-> Coach workspace
-> client list
-> open client
-> current program
-> workout history
-> progress / measurements
-> adherence
-> nutrition summary if permitted
-> assign/change program where permitted
-> client
-> client list
```

Дополнительно: new trainer -> zero state -> invite first client path; assigned/unrelated/former/revoked client security; pending invites; several/long-name clients; recent/no-recent activity.

## Trainer Demo gate

Проверить `landing -> Demo -> trainer scenario -> synthetic clients -> client detail -> program -> history -> progress/measurements/adherence -> temporary action -> persistence interception -> auth/continue`. Никаких production PII, real invitations/notifications/relationships/persistent client writes, AI или Trainer Copilot.

## Marketing accuracy

Landing trainer claims должны соответствовать tasks `21`, `27`, `29`. Не должно быть выдуманных trainer features, Trainer Copilot/AI client-base analysis или fake metrics/social proof.

## Admin release gate

Обязательный flow:

```text
Root/Admin
-> Admin Workspace
-> Overview
-> Users
-> User detail
-> Trainers
-> Trainer detail
-> Relationships
-> AI operational status
-> Audit log
```

Root-only:

```text
Root
-> Administrators
-> assign delegated admin
-> change role
-> deactivate
-> audit entry
```

Negative/capability matrix:

- ordinary user -> admin denied;
- trainer without Admin -> admin denied;
- delegated admin without `admins.manage` -> admin management denied;
- delegated admin -> Root escalation denied;
- admin without Trainer -> Coach workspace denied;
- trainer keeps Personal functionality;
- trainer+admin has separate Personal/Coach/Admin contexts;
- Root source remains `ADMIN_TELEGRAM_USER_IDS`;
- Root receives Trainer only if independently assigned.



## Training product / Fitness Online-inspired release gate

### Program recommendation
Programs -> deterministic wizard -> explanation -> preview -> optional edit -> explicit start. No AI/fake score; manual selection remains.

### RIR
Optional 0/1/2/3/4+, old workouts valid, clear explanation, no readiness/autoprogression claims.

### Exercise
Structured primary/secondary muscles, equipment, alternatives, technique/breathing/mistakes/safety, legal media/source, Web/mobile/TMA, no copied Fitness Online assets/text.

### Analytics
Existing adherence/volume/PR preserved; weight/reps progression, set count, exercise history, optional RIR, muscle exposure without arbitrary coefficient; formulas tested.

### Trainer comments
Coach -> client -> workout -> workout/exercise comment -> client notification -> same in-app context. Unrelated/former access denied; no generic messenger.

### Knowledge
`/knowledge/...` and `/exercises/...` canonical/SEO/internal links/contextual `Что это?`, one reviewed source, no article farm/pharmacology.

### Integrated value
Program -> workout -> nutrition -> progress -> trainer feedback -> knowledge/explanation proves unified product value.

## Unified Web / Telegram visual release gate

Проверить финальный продукт как одну YFC Design System, а не две визуальные версии.

Acceptance:

- Web и TMA используют одинаковые YFC Light/YFC Dark semantic colors;
- Telegram `colorScheme` выбирает Light/Dark, но не перекрашивает feature components через `themeParams`;
- representative Mobile Web и TMA screens на 390/360 имеют одинаковые typography/radii/buttons/cards/forms/spacing/visual hierarchy;
- допустимые отличия TMA объясняются safe area, viewport/keyboard, Telegram BackButton/haptics/auth/deep-links/shell integration;
- desktop Web может использовать отдельную responsive-композицию без отдельного visual language;
- нет Telegram-only component tree или дублированной palette;
- canonical logo/mark одинаков по бренду на Web/TMA и меняется только между approved light/dark variants.

Не считать platform chrome/safe-area различия дефектом. Считать release blocker необоснованный TMA redesign или расхождение основных component styles/colors.

## Authentication release gate

### Web

```text
Landing -> /login -> Telegram -> product
Landing -> /login -> Google -> product
Landing -> /login -> Яндекс -> product
Landing -> /login -> VK ID -> product
```

Apple, если configured, не сломан.

### Continuation

Unauthenticated `/app`, `/coach`, `/admin`, `/join/<token>` -> `/login` -> safe intended destination. No open redirect.

### Telegram Mini App

`signed initData -> automatic auth -> app`, без лишнего provider chooser.

### Identity/linking

- returning/linked provider = same internal account;
- conflict safe;
- no silent email merge;
- Telegram linking safe;
- no secrets client-side;
- Root identity не переносится через linking.

### Session/errors

Refresh restore/expiry/logout/blocked/revocation where supported; provider unavailable/cancel/state/network/conflict дают normalized UI без raw tokens/codes.

### Visual

Landing и `/login` используют один premium language; light/dark; 1440/1280/768/390/360; keyboard/focus/reduced-motion/provider branding.

### SEO

`/login`, reset/verify/callback/error surfaces `noindex` и не в sitemap.

## SEO / Organic Growth release gate

Провести отдельный final SEO regression для production/public surface.

### Crawl/index

Проверить:

- canonical HTTPS host;
- redirects;
- `robots.txt`;
- robots meta;
- sitemap;
- no private/authenticated/admin URLs in sitemap;
- Demo index policy;
- 404/soft-404;
- public page status;
- rendered HTML.

### Metadata/content

Проверить:

- unique meaningful title;
- descriptions;
- one clear H1;
- canonical;
- Open Graph;
- internal linking;
- breadcrumbs where applicable;
- truthful structured data;
- no fake ratings/reviews;
- no stale product claims;
- user + trainer public value propositions.

### Search-engine readiness

Проверить repository/deployment readiness for:

- Google Search Console;
- Yandex Webmaster;
- sitemap submission;
- ownership verification mechanism;
- monitoring runbook.

Не утверждать external verification/submission, если это не подтверждено.

### Content quality

Проверить:

- no mass thin/AI-generated content;
- no keyword doorway pages;
- factual fitness/nutrition claims;
- source/review process where relevant;
- no medical promises;
- no black-hat links.

### Performance

Проверить public-page CWV/lab signals и отсутствие явных regressions.

Field metrics не подменять Lighthouse.

### Organic conversion

Проверить:

```text
organic/public landing
-> product/demo CTA
-> demo/auth continuation
```

и сохранение UTM convention, если campaign params используются.

## Out of scope

Не начинать новый redesign/feature, не менять бизнес-логику ради polish, не делать unrelated refactor, не занижать severity, не добавлять Trainer Copilot и не расширять trainer permissions.



## Проверки

Frontend минимум: typecheck/lint/format/tests/build/relevant Playwright; visual 1440/1280/768/390/360, light/dark/reduced motion. Targeted backend Food/AI/provider-router/security regression по изменённым и critical paths согласно `AGENTS.md`. Проверить отсутствие secrets/debug/temp `.artifacts/` в Git.

## Done when

Нет известных P0/P1 и существенных необъяснённых P2; critical user и trainer flows проходят; Trainer workspace usable как рабочий инструмент; trainer demo показывает реальную ценность на synthetic clients; marketing claims точны; AI не обещан как Trainer Copilot и недоступен в Demo Mode; UI использует единый Web/TMA visual system; финальный отчёт содержит commits/checks/ограничения/оставшиеся P3.

## Рекомендуемый commit

`fix(product): complete integrated user and trainer release audit`

## Процесс и отчёт

Следовать `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`. Работать в текущей feature-ветке, не merge/deploy. Не переходить к следующему task. После изменений запустить только профильные проверки, проверить diff и создать один логический commit. В финальном отчёте перечислить изменения, ключевые файлы, миграции, реально запущенные проверки, ограничения и commit hash.

## Backlog v3 release gates
### Core without AI
Nutrition, programs, workouts, progress, trainer, knowledge, Demo and account flows fully usable with AI disabled.
### Reliability
Offline workout no loss/duplicates; program history coherent.
### Deterministic intelligence
Set kinds, supersets, adaptation, priorities, check-ins, adaptive calories, data confidence.
### AI personalization
Current-user-only tools, nutrition/training/anthropometry context, user-controlled memory, evidence/rationale, Web/TMA conversations, read-only.
### Explicit exclusions
No progress photos/image analysis, social network, generic messenger, Trainer Copilot, autonomous AI writes, pharmacology coaching.

## FINAL RELEASE CANDIDATE GATES

Этот task — последний task до решения о релизе.

### Activation
- new Web user проходит progressive onboarding без redirect loop;
- new TMA user проходит тот же product contract;
- returning user не видит onboarding заново.

### Training
- program selection;
- active workout;
- offline recovery;
- RIR/set types/supersets;
- deterministic progression suggestion;
- workout adaptation;
- program revisions/blocks;
- manual cardio path;
- no pseudo-precise fitness scores.

### Nutrition
- diary/search/custom foods;
- deterministic KBJU;
- adaptive calorie calibration;
- insufficient-data behavior.

### Progress
- weight/measurements;
- priorities;
- confidence-aware trends;
- weekly check-in.

### Trainer
- self Personal context preserved;
- client permissions;
- contextual comments;
- program history;
- notifications.

### Account/privacy
- login/link/unlink semantics;
- export current user data;
- delete account;
- sessions revoked;
- no cross-user leakage;
- no photo feature/data.

### Notifications
- preference/quiet hours;
- dedupe;
- timezone;
- Telegram/in-app deep links;
- no marketing spam.

### AI
- core app works with AI unavailable;
- current-user-only tools;
- nutrition/training/progress/cardio context;
- controlled memory;
- evidence/confidence;
- no autonomous writes;
- no client data in trainer personal Coach;
- no medical/pharmacology/photo analysis.

### Operations
- production config guard;
- health/readiness;
- backup + tested non-prod restore;
- deploy/rollback runbook;
- optional provider degradation;
- useful redacted logs;
- notification/background job observability.

### Release freeze
Не добавлять новые features в рамках этого task.
Только исправлять findings, которые являются:
- release blocker;
- security/privacy blocker;
- data-loss risk;
- broken core flow;
- severe accessibility/performance regression.

Остальные идеи — post-release backlog после реальных пользователей.

## Plain-language beginner release gate

Release blocker if a novice must externally search an unexplained fitness term to complete a core journey.

Manually verify:

`new account -> onboarding -> program -> workout -> normal sets -> progression hint -> food -> measurements -> Progress -> basic AI Coach question`.

Acceptance:
- no mandatory unexplained `RIR`, `adherence`, `deload`, `working set`, `primary exposure` or similar jargon;
- professional terms are secondary or explained;
- advanced controls use progressive disclosure;
- Web and TMA terminology is consistent;
- AI Coach defaults to understandable language.

## Landing reference final gate

Before release, verify the final public Landing against:

- `LANDING_REFERENCE_NOTES.md`;
- `references/landing/landing-reference-dark.png`;
- `references/landing/landing-reference-light.png`;
- canonical brand assets from task `07`.

Acceptance is visual-direction parity, not pixel-perfect copying. Block release for obvious legacy styling, broken light/dark parity, wrong logo variants, fake social proof, stale non-factual pricing/trial/AI claims, broken responsive hierarchy, or Landing/Auth visual mismatch.
