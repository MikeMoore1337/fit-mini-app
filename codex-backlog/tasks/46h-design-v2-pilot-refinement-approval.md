# TASK 46H. Design V2 - refinement пилота и финальный owner checkpoint

- Фаза: **Design V2 pilot verification**
- Приоритет: **46H/93 - owner checkpoint**
- Зависит от: `46G`, ручная проверка и конкретный feedback владельца
- Рекомендуемый reasoning: **High**
- Рекомендуемая модель: **GPT-5.6 Sol High**
- Рекомендуемые skills: `$product-designer`, `$ui-audit`, `$frontend-engineer`, `$qa-engineer`, `$code-reviewer`

## Цель

Проверить реальный Design V2 pilot после ручного тестирования владельцем, исправить только подтверждённые расхождения pilot scope и подготовить окончательный checkpoint перед массовым rollout.

Task можно повторять отдельной Codex-сессией с новым feedback, если владелец после refinement всё ещё не одобрил pilot. Task `46I` запрещено начинать до явного подтверждения.

## Preconditions

В текущем запросе должны быть:

- owner feedback по task `46G`;
- список понравившихся решений;
- список проблем/несоответствий;
- указание, какие расхождения являются блокирующими;
- при наличии screenshots/viewport/state воспроизведения.

Если feedback отсутствует, провести только read-only verification, показать pilot evidence и остановиться без изменений.

## In scope

### 1. Reproduce

Для каждого замечания:

- воспроизвести на указанном viewport/theme/state;
- определить root cause;
- отличить design mismatch от functional/accessibility regression;
- проверить, не затрагивает ли исправление непилотные routes.

### 2. Refine pilot only

Разрешено менять только:

- Design V2 tokens/primitives, уже введённые в pilot;
- AppShell + Today;
- Active Workout;
- Nutrition diary core;
- `/login`/auth entry в pilot scope;
- approved design docs/reference assets, если owner feedback меняет canonical decision.

Не расширять scope на другие экраны.

### 3. Independent UI audit

Проверить фактический render:

- hierarchy;
- typography;
- grid/spacing;
- density;
- responsive;
- cards/surfaces;
- forms/states;
- accessibility;
- motion/reduced motion;
- human-made/AI-pattern tests;
- visual parity с approved references;
- continuity public/auth/app;
- no accidental TMA-only styling.

Severity: P0-P3. Исправить P0/P1 и owner-blocking P2 в pilot scope. Не делать крупный refactor ради P3.

### 4. Regression

Проверить:

- core business behavior не изменён;
- theme persistence;
- navigation/deep links;
- workout state/offline recovery;
- nutrition writes/recovery;
- auth entry/error states;
- non-pilot route smoke;
- typecheck/lint/build/targeted tests.

### 5. Canonical sync

Если feedback изменил утверждённый visual contract, синхронно обновить:

- `docs/design/`;
- approved references;
- component principles;
- responsive/motion rules.

Не оставлять документацию и pilot в разных версиях.

## Out of scope

- полный rollout;
- Landing implementation;
- TMA platform hardening;
- новые features;
- redesign logo без отдельного решения;
- переработка backend/domain logic;
- исправления вне pilot, не вызванные текущим change set.

## STOP CONDITION

После refinement и повторной проверки обязательно остановиться.

Не переходить к task `46I`.
Владелец должен явно написать, что pilot одобрен для rollout.

Если pilot не одобрен, зафиксировать оставшиеся расхождения и продолжить следующей отдельной `46H` сессией, не смешивая rollout.

## Done when

- каждый owner finding воспроизведён и обработан;
- pilot проходит независимый browser/UI audit;
- canonical docs/references синхронизированы;
- targeted regressions green;
- владелец получил чёткий список того, что изменилось и что проверить;
- rollout остаётся заблокированным до явного approval.

## Рекомендуемый commit

При tracked changes:

`fix(ui): refine approved design v2 pilot`

Если изменений нет, commit не создавать.

## Процесс и отчёт

Следовать `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`. Работать в текущей feature-ветке, не merge/deploy. Проверить фактический render через Playwright MCP, выполнить профильные tests, проверить diff и создать один логический commit при изменениях. В финальном отчёте перечислить feedback items, fixes, screenshots, checks, remaining gaps и commit hash, затем остановиться.
