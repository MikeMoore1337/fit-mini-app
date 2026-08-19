# TASK 46I. Design V2 - rollout на выполненный пользовательский интерфейс

- Фаза: **Design V2 core rollout**
- Приоритет: **46I/93 - выполнить перед task 47**
- Зависит от: `46H`, явное подтверждение владельцем pilot
- Рекомендуемый reasoning: **High**
- Рекомендуемая модель: **GPT-5.6 Sol High**
- Рекомендуемые skills: `$commercial-product-builder`, `$product-designer`, `$frontend-engineer`, `$ui-audit`, `$qa-engineer`, `$performance-engineer`, `$code-reviewer`

## Цель

Распространить утверждённый и проверенный Design V2 pilot на все уже реализованные пользовательские surfaces tasks `00-46`, чтобы tasks `47-93` продолжались на едином новом visual foundation без повторного редизайна.

## Preconditions

- task `46H` завершена;
- владелец явно подтвердил pilot;
- `docs/design/` и approved references актуальны;
- критические technical findings tasks `46A-46C` закрыты или owner-approved deferred;
- текущая branch работоспособна.

Без явного pilot approval task не начинать.

## Canonical source of truth

Приоритет:

1. фактический product behavior, security/privacy/SEO/accessibility constraints;
2. approved `docs/design/*v2*` и reference renders task `46F/46H`;
3. verified pilot implementation task `46G/46H`;
4. canonical logo task `07`;
5. legacy visual materials только как historical context.

Старые Landing PNG и старые design-master композиции не переопределяют Design V2.

## In scope

### 1. Shared foundation

Завершить миграцию:

- semantic colors Light/Dark;
- typography/data typography;
- spacing/grid/container;
- radii/borders/shadows/surfaces;
- buttons/inputs/forms;
- navigation;
- cards/lists/tables;
- dialogs/drawers/sheets;
- charts/progress states;
- icons/assets;
- focus/error/success/warning;
- motion/reduced motion;
- loading/empty/error/permission/session states.

Не создавать второй V2 component tree. Удалять legacy tokens/components только после проверки реальных usages.

### 2. Completed surfaces to migrate

Проверить и привести к Design V2 минимум:

- public/auth shell из tasks `13-14`, кроме полного Landing redesign task `73`;
- onboarding;
- AppShell/navigation task `38`;
- Today task `39`;
- Active Workout task `40`;
- Nutrition tasks `41-42`;
- Progress task `43`;
- Programs/Exercises task `44`;
- Program Selection Wizard task `45`;
- Exercise Guide/Encyclopedia task `46`;
- shared mobile composition, которую позже использует TMA task `72`.

Если в коде уже существуют другие user-facing surfaces, созданные до task `46`, включить их только когда они используют тот же shared UI и иначе останутся очевидным legacy fragment. Не расширять feature scope.

### 3. Не входит в rollout

Не выполнять заранее:

- Profile task `47`;
- Coach/Trainer tasks `48-55`;
- Demo/Admin tasks `62-71`;
- Telegram platform integration task `72`;
- production Landing task `73`;
- AI UI task `90`;
- новый logo redesign;
- backend/business changes.

Будущие tasks должны строиться уже на V2 primitives.

### 4. Mobile Web и TMA readiness

Mobile Web должен реализовывать утверждённую mobile composition.

TMA в этой task:

- наследует shared components там, где уже подключён;
- не получает отдельную palette/typography/radii;
- не требует полного Telegram runtime hardening;
- может отличаться только существующими platform adapter details.

Финальный initData/safe-area/BackButton/keyboard/deep-link pass остаётся в task `72`.

### 5. Visual quality

Для каждой migrated surface проверить:

- strong hierarchy;
- appropriate density;
- fewer unnecessary cards/containers;
- purposeful lime;
- varied but coherent composition;
- no generic AI SaaS patterns;
- no accidental visual regression from shared token migration;
- real long/dense/empty/error data;
- light/dark consistency;
- responsive composition, а не уменьшенный desktop.

### 6. Accessibility и performance guard

Не дублировать tasks `74-75`, но не вносить очевидный долг:

- keyboard/focus/contrast/touch targets/reduced motion;
- no overflow/overlap;
- no unnecessary heavy dependency;
- no oversized eager assets;
- no duplicated Web/TMA CSS/component bundles;
- no continuous offscreen animation;
- no material bundle regression без объяснения.

### 7. Verification stages

Работать по вертикальным stages, например:

1. shared primitives;
2. app shell/auth/onboarding;
3. workout/program/exercise;
4. nutrition/progress;
5. cross-surface cleanup/audit.

После каждого stage выполнить только профильные проверки и создать отдельный логический commit согласно `AGENTS.md`, если project workflow это требует.

Browser matrix минимум:

- 1440;
- 1280;
- 768;
- 390;
- 360;
- light/dark;
- representative async/error/empty/validation states;
- reduced motion;
- keyboard/focus.

Артефакты: `.artifacts/design-v2/rollout/`.

### 8. Final independent audit

После rollout применить `$ui-audit` и `$code-reviewer`:

- исправить P0/P1;
- исправить существенные P2 в текущем scope;
- P3 только когда дешёво и не создаёт churn;
- повторно воспроизвести исправленные states;
- проверить отсутствие dead/duplicate legacy CSS/tokens;
- проверить, что future task может переиспользовать V2 без локальной визуальной системы.

## Документация

Обновить `docs/design/` только по фактическим implementation decisions pilot/rollout.

Если candidate token values из task `46F` изменились после browser verification, заменить их проверенными значениями и объяснить причину. Не превращать docs в копию CSS.

## STOP CONDITION

После завершения rollout остановиться.

Не переходить автоматически к task `46J` или `47`.
В финальном отчёте отдельно подтвердить, что Design V2 стал shared source of truth и готов к backlog-синхронизации task `46J`.

## Done when

- все релевантные completed UI surfaces `00-46` используют Design V2;
- legacy styling не остаётся на основных routes без явного обоснования;
- business behavior сохранён;
- Mobile Web готов как общий UI foundation для TMA;
- desktop/mobile/light/dark/states проверены в браузере;
- P0/P1 и существенные rollout P2 закрыты;
- docs/references и реализация согласованы;
- Design V2 готов стать основой future tasks; перед продолжением выполнить task `46J`, которая устранит конфликты в оставшемся backlog.

## Рекомендуемые commits

Примеры по stages:

- `refactor(ui): migrate shared primitives to design v2`
- `feat(ui): roll out design v2 across core surfaces`
- `fix(ui): complete design v2 regression cleanup`

Не создавать искусственно несколько commits, если изменение логически однородно; соблюдать корневой `AGENTS.md`.

## Процесс и отчёт

Следовать `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`. Работать только в текущей feature-ветке, не merge/deploy. После каждого stage выполнить профильные проверки, проверить diff и commits. В финальном отчёте перечислить migrated surfaces, shared primitives, removed legacy pieces, screenshots, checks, limitations и commit hashes.
