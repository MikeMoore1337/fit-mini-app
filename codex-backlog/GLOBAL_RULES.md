# GLOBAL_RULES - общие правила выполнения сабтасков

Этот файл действует для всех задач из `tasks/`.

## Главный принцип

Один task-файл = одна отдельная Codex-сессия = один законченный логический результат.
Не переходить к следующему task автоматически.

## Перед началом каждого task

1. Прочитать корневой `AGENTS.md` и соблюдать его как главный репозиторный контракт.
2. Прочитать этот `GLOBAL_RULES.md`.
3. Проверить текущий код, релевантный `docs/` и последние коммиты затрагиваемой подсистемы.
4. Считать текущий код и Git history источником истины по уже завершённым этапам.
5. Не повторять полный аудит репозитория, если task этого прямо не требует.
6. `masters/` - справочные полные ТЗ. Не читать их целиком по умолчанию. Открывать только релевантный фрагмент, если текущего task недостаточно для продуктового смысла.

## Архитектурные ограничения

- Не переписывать проект с нуля.
- Не делать большой рефакторинг ради красоты, если он не нужен текущей задаче.
- Web и Telegram Mini App остаются двумя поверхностями одного продукта с общей кодовой базой и backend.
- Web, Mobile Web и Telegram Mini App используют одну YFC Design System и одну фирменную пару YFC Light/YFC Dark; TMA отличается платформенной интеграцией, а не отдельной продуктовой палитрой.
- Не создавать второй frontend для Telegram или Web.
- Не дублировать существующие модели, сервисы, формулы или API без доказанной необходимости.
- Детерминированные расчёты должны иметь один источник истины в доменной/backend-логике.
- Не менять бизнес-логику, права доступа или privacy semantics ради UI.
- Не добавлять микросервисы, Redis, поисковый сервер, тяжёлый UI/animation framework или другой инфраструктурный компонент без реальной необходимости.
- Не добавлять обязательные платные внешние зависимости.
- Внешние интеграции должны иметь timeout, безопасные ошибки и локальный/продуктовый fallback там, где это предусмотрено task.

## AI MVP - постоянные ограничения

Для текущего AI Coach MVP:

- `AI_FREE_ONLY=true` - обязательный инвариант.
- Запрещены автоматический paid inference, paid fallback, покупка credits и автопополнение.
- Promotional/trial/free credits не считаются production free tier при `AI_FREE_ONLY=true`; нужен подтверждённый recurring-free режим.
- Персонализированный контекст нельзя отправлять provider/model с неподходящей или неизвестной data policy; при сомнении routing работает fail-closed.
- Provider order по умолчанию: Cloudflare Workers AI -> OrcaRouter -> OpenRouter Free, но порядок конфигурируем.
- Все LLM calls идут только через backend; provider secrets не попадают во frontend/Telegram/Git.
- AI Coach read-only; write tools отсутствуют.
- Streaming, платные embeddings/vector DB, локальная LLM/GPU и обязательный GigaChat не входят в MVP.
- Tool request нельзя отправлять provider/model без подтверждённой capability `tools`.
- Исчерпание/недоступность всех бесплатных подходящих providers заканчивается контролируемой недоступностью, а не расходами.



## SEO / Organic Growth invariants

Для tasks, затрагивающих public Web surface:

- использовать текущие official Google Search Central, Yandex Webmaster, Schema.org и web.dev docs как source of truth;
- не полагаться на SEO folklore, guaranteed ranking claims или third-party "secret factors";
- public indexable content должен быть crawlable, canonical и people-first;
- private/authenticated/user-specific/Coach/Admin data не превращать в поисковые landing pages;
- `robots.txt` не считать заменой `noindex` для доступной HTML-page;
- sitemap содержит только canonical URLs, которые действительно должны индексироваться;
- structured data соответствует visible content; никаких fake ratings/reviews/offers/authors;
- не создавать doorway/thin/programmatic keyword pages;
- не массово публиковать low-value AI-generated content;
- не покупать ссылки, не использовать PBN, link farms, cloaking или spam outreach;
- fitness/nutrition public content должен быть factual, с source/review process для значимых claims и без медицинских обещаний;
- Google Search Console/Yandex Webmaster verification credentials не коммитить;
- client-side behavioral analytics не подключать скрыто как побочный эффект SEO task;
- public URL changes требуют redirect/canonical migration review;
- landing/redesign/performance tasks не должны ломать SEO/public foundation из tasks `02-06` и `09`.


## Fitness Online-inspired training product invariants

- Развивать собственный Your Fitness Coach, не копировать Fitness Online.
- Current code first: не дублировать programs/guides/analytics.
- Program recommendation deterministic/explainable; no LLM selector.
- RIR optional; no RPE/readiness/fatigue inference without validated model.
- Primary/secondary muscles без arbitrary contribution coefficients.
- Analytics formulas/units/missing-data/limitations documented; no pseudoscientific scores.
- Trainer feedback contextual to workout/exercise; no generic messenger. Telegram only notification/deep-link.
- Exercise media only own/legal; no Fitness Online assets/text; no mandatory paid CDN/API.
- Knowledge/exercise pages use reviewed factual source; no mass low-value AI articles.
- No social feed/friends/followers/ratings/trainer marketplace/video calls/sports pharmacology.
- Public knowledge/exercise pages never expose private/custom user data.
- Future AI may use reviewed knowledge/RIR/analytics via separate permissions; no Trainer Copilot here.

## Authentication invariants

- Не создавать вторую auth-систему: существующая multi-provider architecture является foundation.
- Один internal account может иметь несколько verified provider identities.
- Required Web set: Telegram, Google, Яндекс, VK ID.
- Existing Apple сохранять optional, если корректен.
- Email/password остаётся feature-flagged и не включается скрыто.
- Telegram Mini App использует signed `initData` и при valid launch не проходит browser `/login`.
- Canonical browser auth entry - `/login`.
- Landing и `/login` используют один premium public visual language; final Landing task синхронизирует auth shell.
- Auth/private pages `noindex` и не входят в sitemap.
- Provider credentials только server-side; public config без secrets.
- Никакого silent merge по email.
- Identity другого account не переносится автоматически.
- `next` только allowlisted internal path; open redirect запрещён.
- Refresh token не хранить в localStorage.
- Provider protocol details проверять по текущим official docs.
- Root Telegram identity нельзя перенести через account linking.

## Account capabilities и Admin model

```text
Authenticated Account
├── Personal capabilities
├── Trainer capability (optional)
├── Admin capability (optional)
└── Root Admin (server-configured)
```

- Personal functionality - baseline authenticated account.
- Trainer additive: trainer сохраняет свои тренировки, программы, питание, КБЖУ, progress, measurements и AI Coach для собственного разрешённого context.
- Не создавать self trainer-client relationship ради личных данных trainer.
- Admin additive и независим от Trainer.
- Admin не получает Trainer автоматически.
- Trainer + Admin допустимы одновременно при независимом назначении.
- `ADMIN_TELEGRAM_USER_IDS` - server-side source of truth для Root Admin/owner/break-glass.
- Root нельзя создать/удалить/назначить через UI/API/БД.
- Delegated admins назначаются отдельно и работают по least privilege.
- Frontend visibility не является security boundary.
- AI Coach не является Trainer Copilot и не получает client-base данные trainer.

## Demo Mode - постоянные ограничения

- Demo - отдельный application state, не общий database demo-user.
- Demo data/edits временные и не становятся обычными persistent user records.
- Fixtures не содержат персональные или production user data.
- AI Coach в demo полностью недоступен: no chat, no provider calls, no demo AI quota.
- Identity-bound/external-side-effect операции блокируются: invitations, account linking,
  notifications, payments/admin и writes к реальным пользователям.
- UI hiding не является единственной security boundary; применимые ограничения enforce на backend.
- Demo использует тот же app shell/design system и не является вторым приложением.
- Conversion: сначала дать попробовать ценное действие, затем предлагать auth при попытке сохранить.
- Demo -> auth не импортирует fixtures и не перезаписывает real account data автоматически.
- Demo -> Telegram использует existing canonical continuation/deep-link flow; demo state не является Telegram identity.

## Безопасность и приватность

- Все новые endpoint'ы соблюдают текущие auth/RBAC/ownership правила.
- Не доверять идентичности пользователя из frontend или LLM, если она уже определяется серверной сессией/auth context.
- Не логировать секреты, токены, Telegram init data, лишние персональные данные и полный приватный пользовательский контент.
- Не раскрывать внутренние stack traces и сырые upstream errors пользователю.
- Не ослаблять TLS verification.
- Не использовать небезопасный HTML rendering.

## Миграции и данные

- Использовать существующий механизм миграций.
- Не удалять пользовательские данные без прямого требования.
- Не генерировать выдуманный backfill.
- Индексы добавлять только с понятной причиной и реальным query pattern.

## UX/UI

Целевое направление редизайна:

```text
premium sport-tech
graphite / warm neutral / lime
strong typography
clear hierarchy
fewer borders
fewer nested cards
purposeful motion
mobile-first interactions
```

## Brand identity invariants

- Canonical visual reference: `references/brand/your-fitness-coach-logo-reference-light-dark.png`.
- Production logo source of truth is created in task `07`; downstream tasks must reuse it.
- Full logo has light/dark transparent SVG variants.
- Favicon uses only the mark, never the `YOUR FITNESS COACH` wordmark, and must remain readable at 16x16/32x32.
- Do not embed the raster reference inside production SVG, do not keep its white/dark background or glow, and do not add external font/network dependencies to logo SVG.
- Auth, AppShell, Telegram and Landing must not create independent logo variants.
- A downstream redesign may change placement/size, but not redesign the approved mark without an explicit owner decision.

При этом:
- Web и TMA используют одинаковые фирменные YFC Light/YFC Dark colors и semantic tokens;
- Telegram `colorScheme` выбирает YFC Light или YFC Dark, но `themeParams` не создают отдельную продуктовую palette;
- Mobile Web и TMA при одинаковом viewport используют одинаковую типографику, geometry, spacing, components и visual hierarchy; различия допустимы только из-за safe area, viewport/keyboard, BackButton, haptics, auth/deep links и других реальных platform APIs;
- desktop Web может иметь другую responsive-композицию, не становясь отдельным дизайном;
- mobile-first не означает растянутую mobile-композицию на desktop;
- lime использовать дозированно как акцент;
- не превращать интерфейс в glassmorphism/neon/crypto-style;
- motion должен улучшать feedback, а не мешать;
- учитывать `prefers-reduced-motion`;
- не передавать смысл только цветом.

## Артефакты аудита

Audit screenshots, traces, временные отчёты и другие рабочие материалы хранить только в `.artifacts/` и не коммитить. Audit findings не переносить в публичный `docs/`, если это не требуется для долгосрочной технической документации.

## Проверки и Git

После завершения task:

1. Запустить только связанные с ним unit/API/component/e2e/typecheck/lint/build проверки согласно `AGENTS.md`.
2. Не заявлять о проверке, если она реально не запускалась.
3. Проверить `git diff`.
4. Исправить подтверждённые регрессии текущего scope.
5. Не запускать полный suite автоматически, если `AGENTS.md` требует отдельного решения владельца.
6. Сделать один логический commit, если task изменяет tracked files.
7. Для read-only audit без tracked changes commit не создавать.

## Финальный отчёт каждого task

Кратко указать:
- что изменено;
- ключевые изменённые файлы;
- миграции, если были;
- реально запущенные проверки и результат;
- известные ограничения/отложенные вопросы;
- hash commit, если создан.

## Backlog v3 product invariants

- Core app must be fully usable with AI disabled; AI is implemented near the end.
- Deterministic backend first for calculations, program selection, workout adaptation, analytics, sufficiency and energy calibration; AI explains/synthesizes.
- No strong conclusions from sparse data; no magic confidence score.
- Anthropometry compares user mainly with self/priorities; circumference is not a single-muscle measurement; no ideal-body score.
- No progress-photo storage/comparison, computer vision, body-photo analysis or AI image analysis in current backlog.
- AI authoritative facts come from backend tools, not durable text memory. Durable memory stores stable preferences only and is user-controlled.
- Strict per-account AI isolation; trainer personal AI is self-only; Trainer Copilot is out of scope.
- First AI release is read-only; no autonomous program/nutrition/profile writes.
- Product analytics must not contain food contents, exact measurements/macros, trainer comments, AI conversation text, tokens/secrets or unnecessary raw IDs.

## Final pre-release scope freeze

This backlog is the frozen feature scope for the first real-user release.

After task `93`, do not add pre-release product features unless a finding is:
- a security/privacy issue;
- a data-loss/corruption risk;
- a broken core user journey;
- a legal/release blocker;
- a severe accessibility/performance regression.

Everything else goes to the post-release discovery backlog and should be prioritized from real user behavior and feedback.

### Explicitly deferred
- progress photos and all image/body-photo analysis;
- wearables/Health/Strava;
- social feed/friends/followers;
- trainer marketplace;
- generic messenger/video calls;
- Trainer Copilot;
- autonomous AI writes;
- AI-triggered reminders;
- complex readiness/recovery scores;
- advanced sports periodization beyond current blocks.

## Plain-language UX and fitness terminology

The default user-facing language must be understandable to a person with no prior fitness terminology knowledge.

Internal domain/API names may remain technically precise, but a user must not need English jargon,
abbreviations or professional coaching vocabulary to complete core flows.

### Preferred user-facing wording

| Technical / advanced term | Primary UI wording |
|---|---|
| RIR | Повторы в запасе |
| RIR 2 | Осталось примерно 2 повтора |
| Working set | Рабочий подход |
| Warm-up set | Разминочный подход |
| Drop set | Дроп-сет — explain when first used |
| Superset | Суперсет — два упражнения подряд |
| Adherence | Соблюдение плана |
| Deload | Облегчённая неделя / период сниженной нагрузки |
| Progression | Увеличение / прогрессия нагрузки |
| Training block | Тренировочный блок |
| Primary muscle | Основная мышечная группа |
| Secondary muscle | Дополнительная мышечная группа |
| Data confidence / coverage | Достаточно ли данных для вывода |

Do not expose raw internal English values merely because they exist in code.

### RIR

Primary label: `Повторы в запасе`.

Explain:
`Сколько повторов вы ещё могли бы сделать с хорошей техникой после завершения подхода?`

Options:
- `0 — больше не смог бы`
- `1 — ещё примерно 1 повтор`
- `2 — ещё примерно 2 повтора`
- `3 — ещё примерно 3 повтора`
- `4+ — осталось много сил`

`RIR` may appear secondarily as `Повторы в запасе (RIR)`.
It must not be the only beginner-facing label.

### Progressive disclosure

Default workout logging stays simple:
`Вес -> Повторы -> Готово`.

Advanced fields such as repetitions in reserve, set type, drop set, superset and failure
must be optional/progressively disclosed when possible.

### Contextual help

For a non-obvious concept use:
- clear Russian primary label;
- one short helper sentence;
- optional `Что это?` link/dialog to reviewed knowledge.

### Analytics

Do not show raw text such as `RIR coverage insufficient`, `adherence`, `primary exposure` or `confidence score`.

Prefer factual language:
- `Выполнено 10 из 12 запланированных тренировок — 83%`;
- `Пока мало данных об интенсивности: повторы в запасе отмечены только в нескольких подходах`;
- `Рабочие подходы по мышечным группам`;
- `Данных пока мало для уверенного вывода`.

### AI Coach

Coach defaults to natural Russian and unexplained jargon is prohibited.
If the user explicitly uses professional terminology, Coach may mirror it.

### Beginner release acceptance criterion

A novice must be able to complete:

`onboarding -> program -> workout -> nutrition -> measurements -> progress -> basic AI Coach question`

without searching the web for the meaning of a fitness abbreviation or English term.
