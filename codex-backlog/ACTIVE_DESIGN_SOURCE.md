# Активный production source of truth по дизайну

## Текущий статус

```text
ACTIVE_DESIGN = DESIGN_V2
SELECTED_DESIGN = DESIGN_V2_1
DECISION_STATE = OWNER_APPROVED_PENDING_49G
DECIDED_AT = 2026-08-22
```

Утверждённый Design V2 остаётся обязательным production source of truth для Landing, `/login`, authenticated Web, Mobile Web и TMA до закрытия task `49G`.

Tasks `49A/49B` создали alternatives, `49C-49E` закрыли selection/specification/pilot stages. В task `49F` владелец явно утвердил `DESIGN_V2_1`; решение зафиксировано в `.artifacts/design-alternatives/49f/`. Оно выбирает rollout input, но не меняет `ACTIVE_DESIGN`: новый visual direction становится production source только после closure contract task `49G`.

## Порядок источников

Пока task `49G` не закрыт:

1. фактическое product behavior, security, privacy, SEO и accessibility constraints;
2. утверждённые `docs/design/*v2*` и production Design V2 implementation;
3. canonical brand assets task `07`;
4. 49F decision record как разрешённый input только для conditional rollout 49G;
5. 49D specification/renders и 49E pilot evidence только в точном утверждённом scope.

## Финальное решение 49F

```text
FINAL_APPROVE_V2_1: Landing=DESIGN_V2_QUIET_PACE; LOGIN=A_SURFACES_STATES+V2_TYPE+OPTION_1_SPLIT+240PX_CENTERED_AUTH+35PX_CONTINUATION; DESKTOP_APP=V2_CONTENT+A_RAIL+V2_ICONS_TYPE; MOBILE_TMA=V2_COMPACT_FONT_NORMALIZED+BOTTOM_NAV_VIEWPORT_PINNED
```

Для active workout в TMA владелец отдельно выбрал `KEEP_IN_PAGE_BACK`: native Telegram BackButton
не должен дублировать видимый in-page back на этом surface. Полный approved scope, canonical inputs
и непроверенные среды перечислены в `.artifacts/design-alternatives/49f/`.

## Кто может изменить статус

Только task `49F` после явного owner decision может зафиксировать один из статусов:

- `DESIGN_V2`;
- `DESIGN_V2_1`;
- `DESIGN_V3`.

Task `49G` выполняет необходимый conditional rollout, меняет `ACTIVE_DESIGN` только после успешной
проверки и синхронизирует pending backlog. До этого новые renders не являются production acceptance
input для остальных tasks.

## Правило для pending tasks

Tasks `50A`, `50-79` обязаны читать этот файл. Пока `ACTIVE_DESIGN = DESIGN_V2`, они продолжают
использовать Design V2. После закрытия task `49G` они используют только активированный там
canonical scope/docs/renders/tokens `DESIGN_V2_1`.
