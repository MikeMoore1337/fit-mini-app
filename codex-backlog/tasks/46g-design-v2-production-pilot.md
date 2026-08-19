# TASK 46G. Design V2 - production pilot на ключевых экранах

- Фаза: **Design V2 implementation pilot**
- Приоритет: **46G/93 - owner checkpoint**
- Зависит от: `46F`, явное подтверждение владельцем финальных renders
- Рекомендуемый reasoning: **High**
- Рекомендуемая модель: **GPT-5.6 Sol High**
- Рекомендуемые skills: `$product-designer`, `$frontend-engineer`, `$ui-audit`, `$qa-engineer`, `$code-reviewer`

## Цель

Реализовать ограниченный production-quality pilot утверждённого Design V2 на нескольких показательных поверхностях и проверить, что реальный browser render сохраняет качество финальных references.

Это первый этап, на котором разрешено менять production frontend. Полный rollout запрещён до ручной проверки владельцем.

## Критические ограничения

- Реализовать только pilot scope.
- Не мигрировать все экраны и не запускать массовый редизайн.
- Не менять business logic, API contracts, permissions, formulas или data semantics ради визуального результата.
- Не переписывать routing/state architecture без доказанной необходимости.
- Не делать полный production Landing - это task `73`.
- Не выполнять Telegram platform hardening - это task `72`.
- Не создавать отдельные TMA components/styles.
- Не упрощать утверждённую композицию только ради более лёгкой вёрстки.
- Не использовать legacy Landing PNG как implementation target.

## Обязательные источники

Прочитать:

- `docs/design/design-direction-v2.md`;
- `docs/design/design-system-v2.md`;
- `docs/design/component-principles-v2.md`;
- `docs/design/responsive-and-platform-v2.md`;
- `docs/design/motion-v2.md`;
- approved renders из `docs/design/references/design-v2/`;
- фактические current components/tokens/tests.

Если canonical paths отличаются по conventions проекта, использовать созданные task `46F` paths.

## Pilot scope

Реализовать только следующие representative surfaces:

1. Shared Design V2 semantic tokens/primitives, необходимые pilot.
2. AppShell + Today.
3. Active Workout.
4. Nutrition diary core.
5. `/login` или другой существующий public auth entry для проверки brand continuity.

Покрыть минимум:

- desktop 1440/1280;
- tablet 768;
- mobile 390/360;
- light/dark;
- populated;
- loading;
- empty;
- error/retry;
- validation/disabled;
- hover/focus/keyboard;
- reduced motion.

Representative Mobile Web должен соответствовать утверждённой будущей TMA-композиции. Telegram-specific APIs в этой task не добавлять.

## Implementation principles

### 1. Эволюционная миграция

- расширять существующие design tokens/components;
- не создавать второй параллельный component library;
- временная совместимость legacy/V2 допустима только в минимальном объёме pilot;
- явно отметить migration seam для task `46I`;
- не допускать конфликтующих global CSS side effects на непилотных экранах.

### 2. Fidelity

Сохранить approved intent по:

- typography;
- proportions;
- grid/spacing;
- density;
- surface hierarchy;
- lime usage;
- controls;
- navigation;
- charts/data presentation;
- responsive composition;
- motion/reduced motion.

Если reference невозможно реализовать без нарушения accessibility/performance/product truth, выбрать безопасное решение и зафиксировать расхождение.

### 3. Real data and states

Проверять на фактических компонентах и правдоподобных existing fixtures:

- long Russian labels;
- sparse и dense nutrition data;
- active workout с несколькими exercises/sets;
- errors и offline recovery;
- session/auth error;
- empty and first-use states.

Не подгонять дизайн только под идеальные короткие mock values.

### 4. Accessibility

Минимум:

- semantic structure;
- labels/accessible names;
- keyboard/focus order;
- visible focus;
- contrast;
- touch targets;
- reduced motion;
- no meaning by color only.

### 5. Browser verification

После implementation:

1. открыть реальное приложение;
2. снять before/after screenshots;
3. сравнить pilot с approved references;
4. проверить минимум desktop + mobile + light/dark;
5. выполнить один refinement pass;
6. повторить проблемные states после fixes.

Артефакты: `.artifacts/design-v2/pilot/`.

## Tests

Добавить/обновить пропорционально риску:

- component tests;
- targeted integration/e2e;
- visual regression, если уже используется;
- accessibility checks;
- theme/state persistence;
- no regression for non-pilot routes;
- typecheck/lint/build.

Не вводить новый тяжёлый visual testing stack без необходимости.

## Independent review

Перед завершением применить `$code-reviewer` к фактическому diff и проверить:

- accidental global regressions;
- duplicated tokens/components;
- inaccessible handlers;
- broken states;
- layout/performance risks;
- unnecessary scope;
- mismatch with approved Design V2.

## STOP CONDITION

После implementation и browser evidence обязательно остановиться.

Не переходить к task `46H` или `46I`.
Не мигрировать остальные экраны.
Не считать pilot одобренным без ручного запуска и ответа владельца.

В финальном отчёте дать точные команды запуска и список экранов/states, которые владелец должен проверить вручную.

## Done when

- pilot surfaces реализованы в реальном production frontend;
- approved Design V2 воспроизводится в браузере, а не только в mockups;
- непилотные routes не получили необоснованных regressions;
- desktop/mobile/light/dark/states проверены;
- accessibility и targeted tests проходят;
- сделан refinement pass;
- есть owner checkpoint до rollout.

## Рекомендуемый commit

`feat(ui): implement design v2 production pilot`

## Процесс и отчёт

Следовать `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`. Работать в текущей feature-ветке, не merge/deploy. После изменений выполнить профильные проверки, проверить `git diff`, создать один логический commit. В финальном отчёте перечислить reused/changed components, ключевые файлы, screenshots, реально запущенные проверки, known gaps, manual verification steps и commit hash.
