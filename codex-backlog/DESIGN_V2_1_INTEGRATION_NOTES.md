# Design V2.1 — production rollout и backlog alignment

## Решение владельца

Task `49G` выполнила branch B для `DESIGN_V2_1`. Повторный выбор направления не проводился.

```text
SELECTED_DESIGN = DESIGN_V2_1
FINAL_APPROVE_V2_1: Landing=DESIGN_V2_QUIET_PACE; LOGIN=A_SURFACES_STATES+V2_TYPE+OPTION_1_SPLIT+240PX_CENTERED_AUTH+35PX_CONTINUATION; DESKTOP_APP=V2_CONTENT+A_RAIL+V2_ICONS_TYPE; MOBILE_TMA=V2_COMPACT_FONT_NORMALIZED+BOTTOM_NAV_VIEWPORT_PINNED
ACTIVE_WORKOUT_TMA_BACK = KEEP_IN_PAGE_BACK
BLOCKING_MISMATCHES = NONE
REAL_TELEGRAM = NOT_RUN
```

Приоритет источников: фактические product/security/accessibility contracts → решение и owner
overlay `49F` → canonical specification/renders `49D` → pilot evidence `49E`.

## Классификация рабочего дерева при resume

Перед новыми write-действиями `git status --short` содержал только:

| Изменение | Классификация | Решение |
| --- | --- | --- |
| `codex-backlog/telegram-core-release-backlog/tasks/done/02a-production-master-backport.md` (на момент `49G` — untracked) | `HISTORICAL_UNRELATED_USER_CHANGE` | Исторический контекст: не включалась в commit `49G`; позднее task `02A` завершена и архивирована. |

Tracked diff `49G` на этом снимке отсутствовал. Новые изменения, перечисленные ниже, созданы
implementer-pass task `49G` и относятся к `REQUIRED_CHANGE`.

## Rollout gap matrix

| Surface/seam | Статус до rollout | Evidence и минимальное действие |
| --- | --- | --- |
| Landing | `REQUIRED_CHANGE` | Production mobile CSS содержал whole-layout `scale(0.9)`, narrow `scale(0.78)` и `margin-inline: -34px`. Удалено масштабирование/clipping; proof стал in-flow mobile composition без floating desktop decoration. Copy, IA, SEO metadata и desktop Quiet Pace сохранены. |
| `/login` и auth shell | `REQUIRED_CHANGE` | Approved split/track/states существовали только под dev `design_pilot=49e`. Тот же реальный `LoginPage`, provider configuration, redirect validation и errors переведены на canonical V2.1 markup/CSS: `1.04fr/.96fr`, `35px`, `240px`, mobile in-flow. |
| AppShell / desktop navigation | `ALREADY_COMPLIANT` | Поздний production cascade `design-v2.css` уже переопределял legacy `248/284px` на approved rail/content reserve `164/194px`. No-op diff не создан. |
| Today | `ALREADY_COMPLIANT` | V2 content/data/icons/type сохранены; dev-only 49E presentation fragments retired, production content не переработан. |
| Active workout | `ALREADY_COMPLIANT` | Видимый in-page `К сводке` уже существует на root `/app`; router скрывает native Telegram BackButton на root. Добавлен targeted regression proof, platform contract не изменён. |
| Nutrition | `ALREADY_COMPLIANT` | Screen-specific redesign не нужен; используется общий shell/layout contract. |
| Progress | `ALREADY_COMPLIANT` | Screen-specific redesign не нужен; используется общий shell/layout contract. |
| Programs / Exercises | `ALREADY_COMPLIANT` | Screen-specific redesign не нужен; используется общий shell/layout contract. |
| Profile | `ALREADY_COMPLIANT` | Screen-specific redesign не нужен; используется общий shell/layout contract. |
| Coach workspace | `ALREADY_COMPLIANT` | Desktop-first content не менялся; общий AppShell rail уже `164px`. |
| Mobile Web | `REQUIRED_CHANGE` | Не было production snapshot/variables для current/stable viewport и keyboard navigation state. Добавлен общий adapter и CSS contract без второго component tree. |
| TMA shared UI | `REQUIRED_CHANGE` | Production adapter не потреблял `safeAreaInset`, `contentSafeAreaInset`, `viewportHeight`, `viewportStableHeight`, `isActive` и change events. Добавлена нормализация с browser fallback и bounded layout-only updates. |

Coverage matrix не была трактована как требование изменить каждый экран. Content surfaces со
статусом `ALREADY_COMPLIANT` не получили no-op redesign.

## Canonical production source

- `docs/design/design-direction-v2.1.md`;
- `docs/design/responsive-v2.1.md`;
- `docs/design/component-states-v2.1.md`;
- `docs/design/landing-login-v2.1.md`;
- `docs/design/tma-platform-v2.1.md`;
- `docs/design/references/design-v2.1/README.md` и frozen renders с
  `render-manifest.sha256`.

Исторические `docs/design/*v2*` и `docs/design/references/design-v2/` сохранены, но не являются
active acceptance source. Dev-only pilot `49E` удалён из runtime/source; его approval evidence
сохранено без изменений в `.artifacts/design-alternatives/49e-pilot/`.

## Изменённые pending tasks

| Task | Конфликт | Минимальная правка |
| --- | --- | --- |
| `50A` | Могла повторно реализовать adapter, который стал production baseline в `49G`. | Зафиксировано переиспользование adapter и создание harness/smoke без второго layout contract. |
| `73` | Формулировка допускала трактовку финализации Landing как новый redesign. | Явно закреплены active `DESIGN_V2_1`, Quiet Pace и запрет возвращать 49E pilot как source. |
| `74` | Проверка active UI не отделяла V2.1 от historical V2/49E evidence. | Acceptance привязан к фактической V2.1 implementation и canonical paths. |
| `75` | `pre-redesign baseline` мог быть принят за текущий visual source. | Измерения привязаны к active V2.1; historical sources разрешены только как подписанный baseline. |
| `76` | Не было явного release-audit gate на второй visual source/legacy pilot fragments. | Добавлена проверка единственности V2.1 и отсутствия dev pilot branches. |
| `79` | Финальная матрица не требовала проверить отсутствие conflicting legacy visual sources. | Добавлен go/no-go пункт об одном active V2.1 source и отсутствии legacy/pilot fragments. |

Остальные tasks `50-79` уже ссылались на `ACTIVE_DESIGN_SOURCE.md` либо не содержали visual-source
контракта; их functional scope и mobile/TMA acceptance не менялись. Completed task-файлы
`00-49B` и contract `49B1` не переписывались.

## Residual risks и честность evidence

- `REAL_TELEGRAM = NOT_RUN`: real Telegram Android/iOS не проверялись и не считаются пройденными.
- Physical mobile browser и реальная OS keyboard — `NOT_RUN`.
- VoiceOver/TalkBack/screen reader/switch control — `NOT_RUN`.
- Browser text-only `200%` zoom — `NOT_RUN`.
- Field Core Web Vitals и low-end device trace — `NOT_RUN`.
- Browser/Chromium и mocked TMA checks не заменяют эти среды.
- Pre-existing `R49D-11` (`startapp` не сохраняется локальным dev-login) остаётся
  `OUT_OF_SCOPE`; design rollout его не создавал и не исправлял.

Миграции, backend/API/schema/RBAC, dependencies, configuration и production infrastructure не
изменялись. Task `50A` разрешена только в новой сессии после closure `49G`; текущая task её не
начинает.
