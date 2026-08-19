# TASK 71A. Заявка тренера - Profile UX, Admin review, уведомления и activation onboarding

- Фаза: **Trainer activation UX**
- Приоритет: **71A/93 - выполнить сразу после task 71 и до task 72**
- Зависит от: `47`, `48`, `57`, `59`, `68`, `69A`, `70A`, `71`
- Рекомендуемая модель: **GPT-5.6 Sol High**
- Рекомендуемые skills: `$product-designer`, `$frontend-engineer`, `$security-engineer`, `$privacy-engineer`, `$qa-engineer`

## Цель

Завершить сквозной сценарий:

```text
Profile
-> короткая заявка
-> pending state
-> Web Admin Workspace review
-> approved/rejected notification
-> Trainer capability refresh
-> Coach workspace onboarding
```

Перед началом прочитать `TRAINER_APPLICATION_INTEGRATION_NOTES.md`. Использовать готовые backend contracts tasks `69A` и `70A`, не переносить security logic во frontend.

## Пользовательский Profile UX

В разделе Profile создать отдельный блок `Для тренеров`.

### Account без Trainer capability и без заявки

Показать:

- краткое объяснение возможностей кабинета тренера;
- честное описание ручного рассмотрения;
- отсутствие обещания профессиональной верификации;
- CTA `Получить кабинет тренера` или `Подать заявку на доступ`.

Не использовать абстрактное `Изменить роль`.

### Форма

Поля и значения должны соответствовать canonical API task `69A`:

- опыт работы;
- направления работы;
- как планируется использовать приложение;
- примерное количество клиентов - необязательно;
- короткое описание - только если не дублирует предыдущее поле;
- согласие с правилами кабинета тренера.

Требования:

- verified name/contact берутся из account и не требуют повторного ручного ввода без причины;
- beginner-friendly Russian labels;
- field-level validation;
- mobile keyboards/input modes;
- сохранение введённых данных после recoverable error;
- loading/disabled/double-submit protection;
- понятный privacy helper о том, кто увидит ответы;
- никаких дипломов, сертификатов, паспортов и данных клиентов.

### Статусы

Реализовать состояния:

- `pending` - дата подачи, краткое резюме, CTA отозвать;
- `rejected` - user-visible reason, возможность открыть новую форму и подать заново;
- `withdrawn` - возможность подать новую заявку;
- `approved` - подтверждение доступа и CTA `Перейти в кабинет тренера`;
- active Trainer - Coach entry без новой формы;
- suspended/revoked Trainer - использовать current capability UX и не маскировать это новой обычной заявкой.

Не показывать internal note, reviewer identity без необходимости или статус `проверенный тренер`.

## Admin Workspace

Добавить Web-only раздел `Заявки тренеров` отдельно от списка действующих Trainers.

### Queue/list

- pending count в Overview, если metric дешёвый и реальный;
- tabs/filters: новые, одобренные, отклонённые, отозванные;
- pending-first ordering;
- search/pagination;
- applicant name/contact summary;
- дата подачи;
- status;
- previous application indicator;
- clear empty/loading/error/retry states.

### Detail

Показывать:

- applicant account/capability status;
- verified contact identities в разрешённом объёме;
- ответы анкеты;
- previous applications;
- decision history;
- current reviewer conflict/reconciliation state, если backend его вернул.

Не показывать private nutrition, workouts, measurements или client data ради рассмотрения заявки.

### Actions

Для `trainer_applications.manage`:

- `Одобрить` с явным подтверждением последствия - открывается кабинет тренера;
- `Отклонить` с обязательной причиной для пользователя;
- optional internal note отдельно и с понятной видимостью;
- disabled/loading/double-submit protection;
- graceful handling stale status и concurrent reviewer conflict.

Для read-only `support_admin`:

- список и detail без approve/reject;
- internal note скрыт, если backend contract разделяет доступ.

## Уведомления

Переиспользовать task `59`, не создавать второй notification model, scheduler или отдельного support-бота.

Минимум:

- applicant получает подтверждение успешной подачи в приложении;
- reviewers видят новый pending item/count;
- optional уведомление Root/super_admin через существующий Telegram bot/channel допустимо только как notification + safe deep link и с dedupe;
- applicant получает approved/rejected transactional notification;
- rejected notification не раскрывает полный reason на lock screen, а ведёт в безопасный Profile state;
- approved deep link ведёт в Coach workspace/onboarding;
- revoked/deleted/stale destination имеет graceful fallback;
- retries не создают дубликаты.

Не создавать generic support dialog, переписку applicant-admin или ticket system.

## Activation и onboarding

После approve:

- session/capability state обновляется безопасно без обязательного повторного входа, если current architecture это поддерживает;
- navigation показывает отдельные `Для себя` и `Клиенты`/Coach contexts;
- Personal functionality сохраняется;
- первый вход в Coach workspace использует zero state task `48`;
- объясняется путь: пригласить клиента -> клиент принимает -> назначить программу -> отслеживать прогресс;
- автоматически не создаются clients, invitations, relationships или доступ к чужим данным.

## Demo Mode

- Demo user не может отправить persistent application;
- Demo trainer scenario остаётся synthetic fixture и не зависит от approval;
- никаких real admin notifications, capability writes или user records;
- UI показывает корректный auth/conversion boundary вместо ложной отправки.

## Product analytics

Переиспользовать task `57` и записывать только безопасные события, например:

- application entry opened;
- form started;
- submit succeeded/failed с safe reason code;
- withdrawn;
- approved/rejected outcome viewed;
- Coach workspace opened after approval.

Не отправлять ответы анкеты, rejection text, contacts, raw IDs или internal notes.

Admin decision остаётся прежде всего audit event, а не marketing analytics event.

## Responsive, accessibility и states

Проверить минимум 1440/1280/768/390/360:

- keyboard navigation и focus;
- screen reader labels;
- ошибки не только цветом;
- modal/sheet focus trap и return focus;
- long names/answers/reasons;
- empty/partial/loading/error/retry/stale/permission denied;
- reduced motion;
- shared YFC Light/Dark design.

Task `72` отдельно проверит platform-specific TMA behavior, safe area, BackButton, viewport и Telegram deep links.

## End-to-end checks

Минимальный critical matrix:

```text
ordinary user -> submit -> pending -> withdraw -> resubmit
ordinary user -> submit -> super_admin reject with reason -> user sees reason -> resubmit
ordinary user -> submit -> super_admin approve -> Trainer capability -> Personal + Coach
support_admin -> read-only -> no decision action
admin applicant -> cannot self-approve
active Trainer -> cannot submit duplicate application
Demo -> no persistent submission
concurrent/stale review -> graceful conflict, no duplicate capability
```

Дополнительно проверить:

- no application data leakage между accounts;
- no internal note leakage;
- rejected/approved notification dedupe;
- direct admin route/action denied без permission;
- approval не создаёт trainer-client access;
- session refresh/navigation после approval;
- browser reload и returning user states;
- targeted component/Playwright/API integration tests.

## Documentation

Обновить durable user/admin documentation только там, где оно реально существует:

- что заявка открывает кабинет, но не подтверждает квалификацию;
- статусы и повторная подача;
- кто может рассматривать;
- capability/application separation;
- support path при технической проблеме.

Не публиковать внутренние moderation rules, audit payloads или sensitive permission details.

## Out of scope

- professional verification и документы;
- verified badge;
- trainer marketplace, рейтинг и отзывы;
- автоматическое решение или AI scoring;
- appeal/chat/ticket workflow;
- Telegram Admin Workspace;
- generic messenger;
- Trainer Copilot;
- автоматический доступ к client data.

## Done when

Пользователь может понятным способом подать, отозвать и повторить заявку, администратор безопасно рассмотреть её в Web Admin Workspace, решение корректно уведомляет пользователя, approve открывает Coach workspace без потери Personal context, а весь flow не выдаёт ручной доступ за профессиональную верификацию.

## Рекомендуемый commit

`feat(trainer): complete application review and activation experience`

## Процесс и отчёт

Следовать `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`.

Работать только в текущей feature-ветке. Не создавать и не переключать ветки, не merge/rebase и не deploy в production. Не переходить к task `72`.

После изменений запустить только профильные component/API integration/permission/notification/Playwright checks, typecheck/lint/build согласно `AGENTS.md`, проверить `git diff` и создать один логический commit.

В финальном отчёте: user/admin flows, notifications/deep links, capability refresh, analytics, документация, реально запущенные проверки, ограничения/follow-ups и commit hash.
