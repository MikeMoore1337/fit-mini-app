# Активный production source of truth по дизайну

## Текущий статус

```text
ACTIVE_DESIGN = DESIGN_V2
DECISION_STATE = EXPLORATION_PENDING
```

Утверждённый Design V2 остаётся обязательным production source of truth для Landing, `/login`, authenticated Web, Mobile Web и TMA.

Tasks `49A/49B` создали alternatives, `49C-49E` являются decision/specification/pilot stages. Task `49B1` может исправлять только consistency/reuse/responsive defects **внутри текущего Design V2**. Ни одна из этих tasks не меняет `ACTIVE_DESIGN`: новый visual direction становится production source только по owner decision и closure contract.

## Порядок источников

Пока task `49F` не получил явное решение владельца и task `49G` не закрыт:

1. фактическое product behavior, security, privacy, SEO и accessibility constraints;
2. утверждённые `docs/design/*v2*` и production Design V2 implementation;
3. canonical brand assets task `07`;
4. exploration artifacts только как неутверждённые материалы.

## Кто может изменить статус

Только task `49F` после явного owner decision может зафиксировать один из статусов:

- `DESIGN_V2`;
- `DESIGN_V2_1`;
- `DESIGN_V3`.

Task `49G` затем выполняет необходимый conditional rollout и синхронизирует pending backlog. Без обоих условий новые renders не являются production acceptance input.

## Правило для pending tasks

Tasks `50A`, `50-79` обязаны читать этот файл. Если статус остаётся `DESIGN_V2`, они продолжают использовать Design V2. Если task `49F` утвердил другой статус, они используют только перечисленные здесь canonical docs/renders/tokens после закрытия task `49G`.
