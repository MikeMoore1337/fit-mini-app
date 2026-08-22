# GLOBAL_RULES - правила выполнения release backlog v11 resource-aware

Этот файл действует для current task `49B1`, remaining tasks `49C-49G`, task `50A` и tasks `50-79`. Completed tasks `00-49B` не переигрываются.


## Полный task lifecycle

Перед каждой task обязательно прочитать и выполнить `codex-backlog/TASK_EXECUTION_LIFECYCLE.md`.

Фраза владельца `полный task lifecycle` ссылается именно на этот контракт. Он выполняет только основную роль, core/conditional skills и дополнительные lifecycle-роли, которые явно применимы к текущей task, с конечными review/QA циклами и одним логическим commit.

Lifecycle не расширяет scope task и не отменяет owner checkpoints, Trigger/evidence gates, conditional/skip conditions, security/privacy rules или запрет внешних production actions без разрешения.

## Skills: обязательный контракт выбора

Каждая current/pending task начиная с `49B1` задаёт два уровня skills:

- `Рекомендуемые skills` - core skills primary role. Их открыть в начале.
- `Условные skills` - подключать **только** после фактического trigger из task. Не открывать заранее.

Перед работой Codex обязан:

1. прочитать корневой `AGENTS.md`;
2. открыть только core skills текущей task;
3. использовать их как профильные рабочие контракты;
4. открыть conditional skill только если inspection/diff подтверждает его trigger;
5. не расширять scope только потому, что skill описывает более широкую практику;
6. для code/diff `independent-reviewer` использовать `$code-reviewer`, для `qa-verifier` - `$qa-engineer`; не требовать дублировать base skill в каждой task; non-code design/decision gate не загружает `$code-reviewer` автоматически;
7. для обычного review/QA ограничиваться применимым base skill роли и максимум 1-2 профильными skills текущего риска.

Маршрутизация по фактическому scope:

- `$mobile-engineer` + `$frontend-engineer` - нормальная основа client-facing smartphone UI.
- `$telegram-engineer` нужен только при изменении Telegram-specific API/runtime/adapter/initData/BackButton/safe-area/deep-link/real-client behavior. То, что shared UI показывается внутри TMA, само по себе не является trigger.
- `$accessibility-engineer` подключается отдельно при сложном/new interaction, подтверждённом accessibility finding или в dedicated hardening task. Базовые labels/focus/keyboard/touch требования остаются обязанностью frontend/mobile implementation.
- `$fitness-domain-reviewer` нужен, когда меняются fitness/nutrition/cardio/anthropometry формулы, семантика данных или интерпретация. Простое отображение уже утверждённых значений не требует отдельного доменного прохода.
- `$data-engineer` нужен при schema/migration/query/invariant scope; `$backend-engineer` - при реальном backend/API/domain change. Не подключать их только из-за теоретического edge case.
- `$security-engineer`/`$privacy-engineer` подключаются при соответствующей trust/data boundary или dedicated audit, а не на каждый authenticated экран.
- `$product-designer` нужен для реального UX/visual decision; `$ui-audit` - для dedicated visual audit/hardening, а не каждого UI diff.
- `$solution-architect` нужен при cross-system contract conflict/architecture decision, а не для обычной реализации существующего паттерна.

При конфликте соблюдать приоритет: безопасность и приватность -> фактическое поведение продукта -> текущая task -> профильные skills.

## Главный процесс

- Один task-файл = одна отдельная Codex-сессия = один законченный логический результат.
- Работать только в `feature/yfc-platform-v2`.
- Не переходить к следующему task автоматически.
- Перед началом прочитать корневой `AGENTS.md`, этот файл, lifecycle и только текущую task.
- Tasks `00-49B` подтверждены владельцем как завершённые и не выполняются повторно.
- Current task - `49B1`: один production UI consistency/mobile-first normalization checkpoint текущего Design V2 перед owner comparison `49C`.
- После commit `49B1` следующая task - `49C`. Tasks `49C-49G` закрывают оставшуюся часть design alternatives gate; только после `49G` task `50A` создаёт общий mobile/TMA gate.
- `49B1` не выбирает новый visual direction: она исправляет только доказанные inconsistencies текущего active Design V2 и shared component foundation.
- Перед client-facing task прочитать `MOBILE_TMA_FIRST_CONTRACT.md` и применимые пункты `.agents/references/MOBILE_TMA_ACCEPTANCE_MATRIX.md`.
- Не повторять полный аудит репозитория без прямого требования task.
- `masters/`, старые changelog и выполненные task-файлы являются историческим контекстом и не задают pending order.

### Роли lifecycle

`Основная роль` и `Дополнительные роли lifecycle` в task являются точным маршрутом. Не строить автоматическую цепочку `researcher -> reviewer -> QA` и не создавать отдельного агента на каждый skill.

Если следующая task сама является dedicated review/approval gate, не дублировать полный аналогичный review в предыдущей task без явного требования. Примеры: `49B1 -> 49C`, `49E -> 49F`, `78 -> 79`.

### Blocking policy review/QA

- Только `BLOCKER/HIGH` блокируют завершение.
- `MEDIUM/LOW/NIT/OUT_OF_SCOPE` не блокируют commit и не открывают новый workstream.
- Результат `MEDIUM, но коммитить нельзя` запрещён: если task действительно неприемлема, finding должен быть `HIGH/BLOCKER` с воспроизводимым обоснованием.
- Первый independent review - единственный полный review pass. После blocking fix выполняется только targeted recheck закрытого набора finding IDs.
- Обычная task: максимум full review + один targeted recheck; QA - один pass + один targeted recheck при blocking defect. Дополнительные циклы только в исключениях lifecycle.
- Non-blocking finding, требующий migration/schema/API/platform architecture/new dependency/new role/new skill, всегда уходит в follow-up/owner decision.

## Active design source и alternatives gate

- Перед любой visual work прочитать `ACTIVE_DESIGN_SOURCE.md`.
- До явного owner approval и закрытия task `49G` production source остаётся Design V2.
- Tasks `49A` и `49B` уже завершили non-production exploration. Task `49B1` является единственным pre-decision production exception: она может нормализовать только текущий Design V2 без переноса альтернатив.
- Task `49C` не меняет production UI. Tasks `49D-49F` conditional и выполняются только для выбранного V2.1/new direction/explicit hybrid.
- Owner checkpoint нельзя проходить по предположению, похвале или отсутствию замечаний.
- Task `49G` оставляет ровно один active production design source и только затем разрешает task `50A`.
- Новые skills улучшают качество exploration, но не являются доказательством, что V2 нужно заменить.
- Для `49B1-49G` соблюдать применимые части `DESIGN_ALTERNATIVES_EXPLORATION_CONTRACT.md`; `49B1` дополнительно следует своему строгому normalization scope и не импортирует alternative visuals.
- Landing оценивается как две самостоятельные responsive compositions: desktop и mobile.
- TMA остаётся той же mobile product system, а не отдельным visual direction.

## Архитектура

- Не переписывать проект с нуля и не проводить большой рефакторинг ради красоты.
- Web, Mobile Web и Telegram Mini App используют общую кодовую базу, backend и YFC Design System.
- TMA отличается платформенной интеграцией, а не отдельной палитрой, компонентами или бизнес-логикой.
- Не создавать второй frontend, вторую auth-систему или параллельные доменные модели.
- Детерминированные расчёты имеют один источник истины в backend/domain logic.
- Не добавлять Redis, микросервисы, отдельный search server, тяжёлую chart/animation framework или обязательную платную зависимость без доказанной необходимости.
- Внешние интеграции обязаны иметь timeout, ограниченные повторы, безопасные ошибки и предусмотренный fallback.

## Граница первого релиза

До task `79` не входят и не могут становиться скрытыми зависимостями:

- AI Coach и AI provider infrastructure;
- английская локализация;
- импорт программ из XLSX/CSV/TXT/DOCX;
- новостной канал и редакционный конвейер;
- progress photos;
- PWA-installability;
- monetization/entitlements;
- wearables/Health/Strava;
- delegated admin hierarchy;
- native mobile application.

Эти направления находятся только в отдельном post-release backlog. В release UI нельзя показывать фиктивные, locked или `coming soon` entry points для них.

## Product core

Первый релиз оптимизирует связный цикл:

```text
понять план на сегодня
-> быстро выполнить тренировку
-> быстро записать питание
-> увидеть фактическую динамику
-> при необходимости работать с тренером
```

- Today показывает одно главное действие и компактный недельный контекст, но не превращается в notification feed.
- Workout logging по умолчанию остаётся простым: вес, повторы, завершение подхода. RIR, set type и supersets раскрываются дополнительно.
- Active workout должен переживать ожидаемые сетевые сбои без потери подтверждённых действий.
- Nutrition prioritizes recent/favorites/templates/quick add и различает полный, неполный, отсутствующий и осознанно не заполненный день.
- Weekly review и adaptive calorie proposal являются одним пользовательским процессом; изменение цели требует явного подтверждения.
- Progress, nutrition reports и downloadable report являются одной информационной архитектурой, а не конкурирующими верхнеуровневыми разделами.
- Нет social feed, friends, followers, ratings, trainer marketplace, generic messenger, video calls, GPS tracks или универсального readiness score.

## Public knowledge и SEO

- Полная база знаний живёт на Public Web.
- TMA не содержит самостоятельной библиотеки, article index, long-form reader или navigation entry на `/knowledge`.
- В TMA допустимы короткие контекстные объяснения, `Что это?`, техника упражнения и переход на public source только из уместного контекста.
- Public content people-first, reviewed, source-linked и не содержит диагнозов, лечения, спортивной фармакологии или гарантированных результатов.
- Draft/private/user-specific pages не индексируются.
- Sitemap содержит только canonical published URLs.
- Structured data соответствует видимому содержимому; запрещены fake ratings, reviews, offers и authors.
- Не создавать doorway/thin/programmatic pages и не публиковать массовый low-value generated content.
- Изменение public URL требует redirect/canonical review.

## Auth и account capabilities

```text
Authenticated Account
├── Personal capabilities
├── Trainer capability - включается пользователем напрямую
└── Root Admin - только server-configured owner/break-glass
```

- Personal capabilities доступны каждому authenticated account.
- Trainer mode включается из Profile/Settings сразу, без заявки, очереди, беты, ручной модерации, документов или обещания проверки квалификации.
- Trainer capability additive: тренер сохраняет все личные возможности и отдельно получает client workspace.
- Не создавать self trainer-client relationship ради личных данных тренера.
- При работе с клиентом имя и контекст клиента постоянно видимы; опасные действия явно называют клиента.
- Client data доступны только по действующей связи и разрешённому scope.
- Root Admin определяется server-side (`ADMIN_TELEGRAM_USER_IDS` или актуальный эквивалент), не создаётся и не назначается через UI/API/БД.
- До релиза нет delegated admins, support_admin/super_admin hierarchy и управления администраторами.
- Admin и Trainer независимы: Root не получает Trainer автоматически, Trainer не получает Admin.
- Frontend visibility никогда не является security boundary.

## Authentication invariants

- Один internal account может иметь несколько verified identities.
- Required browser providers: Telegram, Google, Яндекс, VK ID. Existing Apple сохраняется optional, если корректен.
- Email/password остаётся feature-flagged и не включается скрыто.
- Valid TMA launch использует signed `initData` и не показывает второй browser login.
- Canonical browser auth entry - `/login`.
- Никакого silent merge по email или автоматического переноса identity другого account.
- `next` только allowlisted internal path; open redirect запрещён.
- Provider credentials только server-side; refresh token не хранится в localStorage.
- Root authority нельзя перенести через account linking.

## Mobile/TMA-first delivery gate

Для Personal и client-facing Trainer flows смартфон является основной средой использования. Каждый pending feature task обязан закрывать свой mobile/TMA acceptance сразу, а не оставлять очевидные regressions до task `72`.

Минимум:

- `360x800`, `390x844`, `430x932`, touch и `hover: none`;
- no horizontal overflow;
- практически удобные touch targets;
- keyboard не перекрывает active field, primary action и recovery;
- fixed/sticky UI учитывает safe area/content safe area;
- light/dark, loading/error/offline/long-content/reduced-motion;
- recoverable state переживает reload/background/temporary network failure, если это релевантно;
- feature-specific scenario добавлен или подтверждён в continuous mobile/TMA smoke task `50A`;
- real Telegram client verification заявляется только если фактически выполнена.

Coach/Admin сложные рабочие пространства могут быть desktop-first. Это должно быть явно указано в task; mobile smoke остаётся обязательным, а Admin не появляется в TMA без отдельного решения.

## TMA product contract

TMA оптимизирован для быстрых мобильных действий:

- открыть Today;
- начать/продолжить/завершить тренировку;
- отметить подходы и отдых;
- быстро записать питание;
- посмотреть краткий Progress/итог;
- открыть технику упражнения;
- перейти к профилю и необходимым настройкам.

Не добавлять в TMA:

- отдельную базу знаний;
- длинное чтение статей как основной сценарий;
- дублирующий Telegram-only frontend;
- отдельную Telegram product palette;
- platform controls, дублирующие понятные shared controls без UX-причины.

## Demo Mode

- Demo использует ровно подготовленные безопасные сценарии из tasks `68-69`.
- Demo - отдельное временное application state, не общий database demo-user.
- Fixtures не содержат production/user data.
- Demo edits не импортируются в реальный аккаунт.
- Invitations, account linking, product notifications, Admin actions и writes к реальным пользователям блокируются server-side.
- Demo использует тот же UI и не становится вторым приложением.

## Data confidence и fitness safety

- Не делать сильных выводов из редких данных и не изобретать magic score.
- Anthropometry сравнивает пользователя прежде всего с собой; окружность не объявляется размером отдельной мышцы.
- Не интерполировать отсутствующие замеры и не считать пропущенное питание нулём.
- Strength volume и cardio metrics не смешиваются.
- Program selection, progression, workout adaptation, analytics и calorie calibration детерминированы и объяснимы.
- Не добавлять diagnosis/treatment, sports pharmacology, body-photo analysis или autonomous program/nutrition changes.

## Privacy и безопасность

- Все endpoint'ы соблюдают current auth/RBAC/ownership.
- Не доверять user identity или target user id из frontend, если контекст определяется серверной сессией.
- Не логировать secrets, tokens, Telegram init data, полные private notes, food contents, exact measurements или trainer comments без отдельной доказанной необходимости.
- Не показывать stack traces и raw upstream errors.
- Не ослаблять TLS verification и не использовать unsafe HTML rendering.
- Export/delete/report links не раскрывают чужие данные и имеют ограниченный lifecycle.

## Миграции и данные

- Использовать существующий Alembic/data migration mechanism.
- Не удалять пользовательские данные и не генерировать выдуманный backfill без прямого требования.
- Исторические nutrition targets имеют период действия; отчёты используют цель, действовавшую в конкретную дату.
- Индексы добавляются только под реальный query pattern.
- File/artifact generation ограничена по размеру и времени, хранение временное и документированное.

## UX и Design V2

Целевое направление:

```text
premium sport-tech
warm neutral / graphite / lime
strong hierarchy
one primary action
fewer nested cards
mobile-first interaction
purposeful motion
```

- Default UI понятен новичку; профессиональные детали раскрываются постепенно.
- Не передавать смысл только цветом.
- Поддерживать keyboard, focus, labels, contrast и `prefers-reduced-motion`.
- Loading, empty, partial, error, offline и long-data states являются частью acceptance criteria.
- Не добавлять локальные palette/card/button systems поверх shared Design V2.


## UI consistency contract

Для любой pending client-facing UI task действуют эти правила независимо от того, загружен ли `$product-designer` или `$ui-audit`:

- active design source, shared design tokens и существующие primitives/components являются первым source of truth;
- одинаковый **semantic** control/pattern должен использовать тот же shared component и именованный variant/size/state, если нет явной UX/responsive/platform причины отличаться;
- не создавать локальный button/input/card/badge/tab/dialog/navigation primitive, если существующий shared primitive можно разумно переиспользовать или минимально расширить;
- colors, typography, spacing, radii, borders, shadows, icon sizes и interaction states брать из активной системы, а не создавать экранные мини-системы;
- raw values допустимы для действительно уникальной геометрии, но не должны дублировать уже существующий token или создавать случайное расхождение повторяющегося паттерна;
- повторяющийся UI pattern должен иметь один поддерживаемый source of truth; при этом не абстрагировать семантически разные элементы только из-за внешнего сходства;
- Mobile Web и TMA используют те же visual/component primitives; platform-specific safe area, keyboard, BackButton, haptics и chrome не являются основанием для отдельного visual system;
- Personal/client-facing composition проектируется и проверяется mobile-first; desktop может иметь другую композицию, но не другой набор случайных primitives;
- новая feature-task проверяет consistency только изменённой поверхности и непосредственных usages shared component - **не запускает новый product-wide UI audit**;
- явная consistency regression текущего diff считается обычным defect текущей task; severity определяется реальным impact и acceptance criteria, а не автоматически повышается до `HIGH`.

Dedicated product-wide consistency audit после смены правил/дизайн-системы выполняется task `49B1`. После её закрытия будущие задачи обязаны сохранять baseline, а не повторять этот аудит.

## Plain-language contract

Primary labels:

| Internal term | User-facing Russian |
|---|---|
| RIR | Повторы в запасе |
| working set | Рабочий подход |
| warm-up set | Разминочный подход |
| drop set | Дроп-сет - объяснить при первом использовании |
| superset | Суперсет - два упражнения подряд |
| adherence | Соблюдение плана |
| deload | Облегчённая неделя |
| progression | Увеличение нагрузки |
| data confidence | Достаточно ли данных для вывода |

Не показывать raw internal English values только потому, что они существуют в коде.

## Проверки и Git

После task:

1. Запустить только связанные unit/API/component/e2e/typecheck/lint/build проверки по `AGENTS.md`.
2. Не заявлять проверку, если она фактически не запускалась.
3. Проверить `git diff`, migrations и config changes.
4. Исправить все `BLOCKER/HIGH` текущего scope; `MEDIUM/LOW/NIT/OUT_OF_SCOPE` не использовать как основание расширить task.
5. После blocking fix повторить только affected checks/recheck, а не полный audit.
6. Не запускать полный suite автоматически, если его не требует task/доказанный риск.
7. Создать один логический commit при tracked changes, даже если остались документированные non-blocking findings.
8. Для read-only audit без изменений commit не создавать.

Финальный отчёт содержит: reused, changed, key files, migrations/config, exact checks, limitations/follow-ups и commit hash.

## Beginner release acceptance

Новичок без внешнего поиска терминов способен пройти:

```text
registration
-> onboarding
-> choose program
-> complete workout
-> log food
-> add measurement
-> understand Progress
```

Тренер способен напрямую включить Trainer mode, пригласить тестового клиента, назначить программу, увидеть выполнение и оставить контекстный комментарий.

## Scope freeze

После task `79` до решения о релизе добавляются только исправления:

- security/privacy;
- data loss/corruption;
- broken core journey;
- legal/release blocker;
- severe accessibility/performance regression.

Все остальные идеи попадают в post-release backlog и приоритизируются по фактическому поведению и обратной связи пользователей.

## Выполненные tasks и новые skills

Tasks `00-49B` не выполнять повторно из-за обновления `.agents`, новых skills или нового design exploration. Task `49B1` является отдельным ограниченным checkpoint для уже накопленной UI consistency/mobile-first normalization; она не переигрывает функциональные acceptance criteria выполненных tasks. Поздняя task `76` остаётся release-stage retrospective audit и не является причиной откладывать доказанные UI consistency defects из `49B1`. Реальные usability sessions - task `77`; production readiness - task `78`; final go/no-go - task `79`. Новый skill сам по себе не разрешает refactor без прямого требования текущей task или доказанного blocking defect.
