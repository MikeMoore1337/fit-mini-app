# TASK 48. Кабинет тренера и работа с клиентами

- Фаза: **Core UX**
- Приоритет: **48/93**
- Зависит от: `21`, `26`, `27`, `30`, `32`, `34`, `38`, `43`, `44`
- Рекомендуемый reasoning: **Medium/High**
- Рекомендуемые skills: `$product-designer`, `$frontend-engineer`

## Цель

Сделать Coach workspace полноценным рабочим инструментом персонального тренера, а не просто списком клиентов.

Тренер должен за несколько секунд понимать состояние client base: сколько активных клиентов, кто тренировался недавно, кто давно не проявлял активности, у кого появились новые результаты, как соблюдается план и кому нужно открыть подробный прогресс.

Продукт должен стремиться заменить разрозненный workflow «мессенджер + таблицы + заметки + отдельные трекеры» единым пространством Your Fitness Coach.

## In scope

Переработать overview, clients list/search/filters, pending invites/invite flow, client row/card/detail, program assignment/edit entry, training/progress summary, nutrition/adherence summary если разрешено, navigation between coach/client contexts.

Desktop эффективно использует пространство и scanability. Mobile не копирует table, использует high-signal rows/cards + overflow menu. Client detail: identity/status -> active program -> next/recent workouts -> progress -> nutrition/adherence if allowed -> actions. UI не является security boundary.


## Coach dashboard и trainer productivity

Верхний уровень Coach workspace должен быть рабочим dashboard, а не декоративной сеткой cards. Использовать только фактические high-signal данные из task `21`. Где данные доступны, показывать:

- количество активных клиентов;
- pending invitations;
- recent activity / objective no-recent-activity signal;
- последние PR/значимые результаты;
- training adherence;
- nutrition adherence только при разрешённом access;
- последние updates measurements.

Не создавать subjective/AI client scores: motivation, dropout risk, readiness, recovery и подобные.

## Trainer onboarding / zero state

Для тренера без клиентов показать полезный onboarding: пригласить первого клиента -> установить связь -> назначить программу -> отслеживать тренировки и прогресс. CTA приглашения должен быть очевидным. После появления клиентов onboarding не должен доминировать.

## Quick actions

Минимизировать переходы для частых действий: пригласить клиента, открыть клиента, открыть/назначить/изменить программу, посмотреть тренировки, progress, measurements и разрешённое nutrition/adherence.

## Program workflow

Использовать общий program experience из task `44`, не дублировать отдельный builder внутри Coach workspace. Обеспечить предсказуемую навигацию `Coach -> Client -> Program -> Client -> Client list` и не терять search/filter state без необходимости.

## Personal vs Trainer context

Trainer capability является additive и не заменяет Personal functionality.

Trainer сохраняет собственные:

- тренировки;
- программы;
- питание;
- КБЖУ;
- progress;
- measurements;
- AI Coach для собственного поддерживаемого контекста.

Coach workspace используется только для работы с закреплёнными клиентами.

Не создавать self trainer-client relationship ради собственных данных trainer.

Явно различать Personal/`Для себя` и Coach/`Клиенты`. При открытии клиента всегда должно быть понятно, чьи данные сейчас просматриваются или редактируются.

## Contextual feedback
Backend task `26` является trainer productivity feature; interaction task `49`. Coach должен иметь entry points из client workout/history к feedback, но без chat inbox.

## Extended training analytics
Client detail может использовать exercise progression/completed sets/volume/optional RIR/muscle exposure task `27`; client list не тянет full history.

## AI boundary

Текущий AI Coach MVP предназначен для самостоятельного пользователя. Не добавлять Trainer Copilot, AI summaries client base, AI program generation и не отправлять client data в LLM ради Coach workspace.

## Design V2 contract

Coach workspace развивает утверждённую Design V2, а не вводит отдельную admin/SaaS dashboard-систему. Перед UI-работой прочитать `codex-backlog/DESIGN_V2_INTEGRATION_NOTES.md` и релевантные `docs/design/*v2*`; переиспользовать shared shell, navigation, buttons, forms, data regions, semantic colors, typography, geometry и icon language. Desktop и mobile могут иметь разную композицию, но остаются одним продуктом; существенные visual changes проверить в реальном браузере в light/dark и не менять канонический дизайн без owner checkpoint.

## Out of scope

Не менять relationship model, не расширять trainer data access, не добавлять marketplace/chat/video/Trainer Copilot/AI client analysis и не ослаблять backend permissions.



## Проверки

Zero clients + first-client onboarding, pending invites, several/many/long names, recent/no-recent activity, search/filters, client detail, assign/edit program, client->program->client, allowed nutrition/progress, assigned/unassigned/former/revoked access, mobile 390/360, desktop 1440, targeted Playwright и отсутствие obvious N+1.

## Done when

Coach workspace выглядит частью продукта и реальным productivity hub: trainer быстро понимает состояние client base, частые actions требуют минимум переходов, zero state мотивирует пригласить первого клиента, desktop продуктивен, mobile usable, данные посторонних клиентов недоступны.

## Рекомендуемый commit

`feat(ui): make coach workspace a productive trainer hub`

## Процесс и отчёт

Следовать `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`. Не переходить к следующему task. После изменений запустить только профильные проверки, проверить diff и создать один логический commit. В финальном отчёте перечислить изменения, ключевые файлы, миграции, реально запущенные проверки, ограничения и commit hash.

## Backlog v3 integration: trainer longitudinal context
Coach workspace может показывать current block, recent revision, weekly check-in и confidence-aware summaries. AI client analysis/Trainer Copilot не входит в scope.
