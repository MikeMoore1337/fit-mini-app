# Активный production source of truth по дизайну

## Текущий статус

```text
ACTIVE_DESIGN = DESIGN_V2_1
SELECTED_DESIGN = DESIGN_V2_1
DECISION_STATE = ACTIVE_PRODUCTION_AFTER_49G
DECIDED_AT = 2026-08-22
ACTIVATED_AT = 2026-08-22
```

`DESIGN_V2_1` — единственный active production source для Landing, `/login`, authenticated Web,
Mobile Web и TMA. Tasks `49A-49F` являются historical exploration/decision/evidence; их artifacts
не создают второй active visual source. Design V2 docs/renders сохранены как historical baseline.

## Точное решение владельца

```text
FINAL_APPROVE_V2_1: Landing=DESIGN_V2_QUIET_PACE; LOGIN=A_SURFACES_STATES+V2_TYPE+OPTION_1_SPLIT+240PX_CENTERED_AUTH+35PX_CONTINUATION; DESKTOP_APP=V2_CONTENT+A_RAIL+V2_ICONS_TYPE; MOBILE_TMA=V2_COMPACT_FONT_NORMALIZED+BOTTOM_NAV_VIEWPORT_PINNED
ACTIVE_WORKOUT_TMA_BACK = KEEP_IN_PAGE_BACK
BLOCKING_MISMATCHES = NONE
REAL_TELEGRAM = NOT_RUN
```

Для active workout в TMA сохраняется видимый in-page back, а native Telegram BackButton скрыт,
чтобы не дублировать navigation control. Для остальных nested routes/overlays действует canonical
TMA platform contract.

## Canonical DESIGN_V2_1 paths

1. `docs/design/design-direction-v2.1.md` — specification, tokens и component contracts.
2. `docs/design/responsive-v2.1.md` — breakpoints, rail/mobile geometry и layout formulas.
3. `docs/design/component-states-v2.1.md` — shared components и state matrix.
4. `docs/design/landing-login-v2.1.md` — Landing и `/login` contract.
5. `docs/design/tma-platform-v2.1.md` — shared Mobile Web/TMA platform contract.
6. `docs/design/references/design-v2.1/README.md` — approved render index;
   `render-manifest.sha256` фиксирует exact bytes.
7. `codex-backlog/DESIGN_V2_1_INTEGRATION_NOTES.md` — rollout gap matrix, backlog alignment и
   residual risks.

## Порядок источников

1. фактические product/security/privacy/accessibility/SEO contracts и verified behavior;
2. этот active source и перечисленные canonical `DESIGN_V2_1` docs;
3. фактическая shared production implementation и tests;
4. frozen V2.1 renders как hierarchy/composition evidence;
5. Design V2 docs/renders только как historical baseline;
6. `.artifacts/design-alternatives/49d-selected-candidate/`, `49e-pilot/` и `49f/` только как
   historical approval/evidence packet.

Static renders и mocked TMA не доказывают OAuth, assistive technology, physical keyboard, field
performance или real Telegram Android/iOS. `REAL_TELEGRAM = NOT_RUN` остаётся residual risk.

## Правило для pending tasks

Tasks `50A`, `50-79` обязаны читать этот файл и использовать только canonical `DESIGN_V2_1`
paths плюс фактическую implementation. Они не возвращают 49E pilot, не выбирают новый visual
direction и не трактуют coverage matrix task `49G` как требование переработать каждый экран.

Изменить active source после closure `49G` можно только отдельным owner-approved design task.
