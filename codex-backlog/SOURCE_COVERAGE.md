# Покрытие исходных ТЗ

Этот файл показывает, куда в текущей нумерации перенесены крупные исходные требования. Источник истины по порядку выполнения - `00_START_HERE.md` и каталог `tasks/`.

## Brand / Logo / Favicon

| Требование | Текущий task |
|---|---|
| Утверждённый light/dark logo reference | `07` |
| Production SVG light/dark | `07` |
| Читаемый mark-only favicon без `YOUR FITNESS COACH` | `07` |
| Unified YFC Light/Dark theme contract for Web/TMA + canonical logo switching | `08` |
| Auth brand reuse | `13` |
| AppShell brand reuse | `38` |
| Telegram brand reuse | `72` |
| Landing/Auth final brand parity | `73` |
| Approved dark/light Landing references and composition | `73` |
| Reference-bound Hero/capabilities/showcase/client-trainer/demo/platform/FAQ/footer | `73` |
| No invented testimonials/pricing/claims from visual references | `73`, `93` |
| Responsive brand QA | `74` |
| Brand asset performance QA | `75` |
| Final release brand regression | `93` |

## Food + Training Platform

| Исходный блок | Текущий task |
|---|---|
| Read-only platform audit | `00` |
| Food domain / products / provenance / system foods | `15` |
| Food diary backend/API/timezone | `16` |
| User foods / recent / favorites / local search | `17` |
| Recipes / meals / copy day/meal/product | `18` |
| External food provider / Open Food Facts adapter | `19` |
| Barcode lookup backend | `20` |
| Progress/adherence/trainer backend | `21` |
| Food platform hardening | `22` |
| Camera/manual barcode + discovery UI | `42` |
| Today dashboard | `39` |
| Training analytics extension | `27` |
| Progress UX | `43` |
| Trainer workspace | `48` |
| Nutrition UI | `41-42` |

## Training product expansion

| Требование | Текущий task |
|---|---|
| Exercise/muscle domain | `23` |
| RIR / workout set foundation | `24` |
| Deterministic program selection | `25` |
| Trainer contextual comments backend | `26` |
| Training analytics | `27` |
| Exercise media foundation | `28` |
| Advanced set semantics / supersets | `29` |
| Program versioning / blocks | `30` |
| Body priorities / anthropometry | `31` |
| Data quality/confidence contract | `32` |
| Adaptive energy calibration | `33` |
| Weekly check-in | `34` |
| Deterministic workout adaptation | `35` |
| Offline-safe active workout | `36` |
| Product analytics foundation | `37` |
| Knowledge base integration | `50` |

## Premium Redesign / Product UX

| Исходный этап | Текущий task |
|---|---|
| Baseline UI audit | `01` |
| Design system | `05` |
| Canonical brand assets | `07` |
| Theme contract | `08` |
| App shell/navigation | `38` |
| Today | `39` |
| Active workout | `40` |
| Nutrition | `41-42` |
| Progress | `43` |
| Programs/exercises | `44-46` |
| Profile/account | `47` |
| Coach workspace | `48` |
| Trainer comments UX | `49` |
| Knowledge contextual integration | `50` |
| Advanced UX / calibration / blocks / anthropometry / confidence / analytics | `51-57` |
| Telegram platform integration over shared YFC UI | `72` |
| Landing | `73` |
| Responsive/a11y/states | `74` |
| Performance/motion | `75` |
| Final audit | `93` |

## Multi-provider AI Coach

| Исходный блок/этап | Текущий task |
|---|---|
| Audit + architecture | `76` |
| Provider abstraction / free-only guard | `77` |
| Cloudflare Workers AI | `78` |
| OpenRouter Free | `79` |
| OrcaRouter Free | `80` |
| Router / failover / cooldown | `81` |
| Topic/domain policy gate | `82` |
| App knowledge retrieval | `83` |
| Read-only tools / agent loop | `84` |
| Nutrition context tools | `85` |
| Training/progress/anthropometry context | `86` |
| Personalized memory/user context | `87` |
| Evidence/confidence/rationale | `88` |
| Conversations/API/telemetry | `89` |
| Shared Web/Telegram AI UI | `90` |
| Threat model/security/evals/docs | `91` |
| Telegram platform/runtime hardening without separate visual design | `72` |
| Final integrated regression | `93` |

## Demo Mode

| Исходный Demo block | Текущий task |
|---|---|
| Audit/design | `62` |
| Foundation | `63` |
| Fixtures/ephemeral interactions | `64` |
| UX/conversion | `65` |
| Auth handoff/migration | `66` |
| Security/restrictions | `67` |
| Final verification | `68` |
| Landing demo presentation | `73` |
| Final release gate | `93` |

Original demo package сохранён в `masters/demo-mode/`.

## Admin capability evolution

- `69` Root/capability foundation.
- `70` Admin operations backend + audit.
- `71` Web Admin Workspace.
- `73` final landing marketing where admin is not a public value proposition unless explicitly relevant.
- `93` final User/Trainer/Admin/Demo/AI regression gate.

Root source of truth: `ADMIN_TELEGRAM_USER_IDS`.

## SEO / Organic Growth block

- `02` SEO + organic growth baseline audit.
- `03` technical SEO/indexation foundation.
- `04` Search Console/Yandex Webmaster monitoring readiness.
- `06` public SEO IA/content foundation.
- `07` canonical brand assets for public/share surfaces.
- `09` organic promotion/distribution foundation.
- `73` final Landing must preserve SEO.
- `75` Core Web Vitals/performance.
- `93` final SEO release gate.

Official-source policy: Google Search Central, Yandex Webmaster, Schema.org, web.dev.

## Authentication block

- `10` audit.
- `11` identity/session/linking.
- `12` provider readiness.
- `13` premium `/login`.
- `73` Landing/Auth final visual parity.
- `93` final auth regression gate.

## Fitness Online-inspired expansion

Current repo inspection informs tasks `23-30`, `43-50`, `54-58`: existing exercise guide/analytics/programs are extended rather than rebuilt; RIR/comments/knowledge gaps are added explicitly. The product remains Your Fitness Coach and is not positioned as a clone of Fitness Online or FatSecret.
