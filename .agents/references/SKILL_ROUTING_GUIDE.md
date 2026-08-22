# Skill routing guide v5 - core/conditional

## Два уровня skills

- `Рекомендуемые skills` в task - core skills primary role. Загружать в начале.
- `Условные skills` - загружать только после фактического trigger, указанного task.
- Для code/diff review base skill - `$code-reviewer`; для QA - `$qa-engineer`. Non-code design/decision reviewer не загружает `$code-reviewer` автоматически. Base skills не обязаны повторяться в task.
- Skill никогда не расширяет scope.

## Маршрутизация по фактическому изменению

| Изменение | Обычно достаточно | Подключать дополнительно только при trigger |
|---|---|---|
| Client-facing smartphone UI | `$frontend-engineer` + `$mobile-engineer` | `$telegram-engineer` при Telegram-specific runtime/API; `$accessibility-engineer` при сложном interaction/a11y finding |
| Shared desktop UI | `$frontend-engineer`; `$product-designer` если есть UX/visual decision | `$mobile-engineer` если тот же flow обязан быть smartphone-first |
| Telegram platform | `$telegram-engineer` + `$mobile-engineer` | `$security-engineer` при trust boundary/initData/auth |
| Backend/API/domain logic | `$backend-engineer` | `$data-engineer` при schema/query/invariant; `$security-engineer` при auth/permission boundary |
| DB/migration | `$data-engineer` + `$backend-engineer` | `$privacy-engineer` при sensitive lifecycle/retention/export/delete |
| Fitness/nutrition/cardio semantics | `$fitness-domain-reviewer` + фактический implementation skill | Не нужен отдельный domain pass для простого отображения уже утверждённых значений |
| Public evidence content | `$evidence-content-editor` | `$seo-auditor` если меняется public discoverability/metadata/indexation |
| Landing composition | `$landing-art-director` + `$product-designer` + `$frontend-engineer` | `$seo-auditor`, `$performance-engineer` по фактическому scope |
| Dedicated UI hardening | `$ui-audit` / `$accessibility-engineer` / `$performance-engineer` по цели task | Не загружать все три автоматически |
| Release/operations | `$release-manager` + `$platform-engineer` | security/privacy/observability streams только по task/risk |

## Важные исключения

### TMA

То, что shared React UI запускается внутри Telegram Mini App, не означает автоматический `$telegram-engineer`. Он нужен, когда меняется Telegram-specific contract: `initData`, `BackButton`, viewport/safe area events, platform deep-link adapter, Telegram auth/runtime или real-client compatibility.

### Accessibility

`$frontend-engineer` и `$mobile-engineer` обязаны соблюдать базовые labels, focus, keyboard/touch и semantic controls. Отдельный `$accessibility-engineer` нужен для dedicated hardening, сложного нового interaction или подтверждённой проблемы.

### QA/review

Не включай `$qa-engineer` и `$code-reviewer` в core skill list каждой feature-task. `$qa-engineer` загружается при назначенном QA; `$code-reviewer` - при назначенном code/diff review, но не для purely design/decision gate.

### Architecture

Не подключай `$solution-architect` для обычного использования существующих contracts. Он нужен при реальном cross-system conflict, новой архитектурной границе или explicit architecture/audit task.

## Бюджет контекста

Для обычной implementation task старайся удерживать core набор примерно в 2-5 skills. Review/QA pass - base skill роли + максимум 1-2 профильных skills. Большие audit/release tasks загружают skills последовательно по независимым streams, а не все сразу.
