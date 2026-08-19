# TASK 46F. Design V2 - утверждённое направление, финальные рендеры и спецификация

- Фаза: **Design V2 approval**
- Приоритет: **46F/93 - owner checkpoint**
- Зависит от: `46E`, явный выбор и замечания владельца
- Рекомендуемый reasoning: **High**
- Рекомендуемая модель: **GPT-5.6 Sol High**
- Рекомендуемые skills: `$product-designer`, `$product-discovery`, `$ui-audit`, `$technical-writer`; `$frontend-engineer` только для изолированных render prototypes

## Цель

Собрать одно финальное Design V2 направление из выбранной концепции и явных замечаний владельца, показать полный набор согласованных рендеров и зафиксировать долговременный visual source of truth до изменения production frontend.

## Preconditions

В текущем запросе Codex должны быть явно указаны:

- выбранное направление из task `46E`;
- элементы других направлений, которые нужно использовать;
- замечания по цвету, типографике, композиции, density, components и mobile;
- что обязательно сохранить из текущего продукта;
- что владелец точно отклоняет.

Если feedback отсутствует или неоднозначен, не выбирать за владельца и не начинать task.

## Критические ограничения

- Не менять production frontend, styles, tokens, components, routes или business logic.
- Не начинать pilot/rollout.
- Не расширять продуктовую функциональность.
- Не возвращаться к старым Landing PNG как к композиционному source of truth.
- Не создавать отдельный design для TMA.
- Не маскировать нерешённые UX-проблемы красивыми mockups.
- Финальные references должны быть реалистично реализуемы в текущем стеке и при реальной data density.

## In scope

### 1. Объединение owner feedback

Составить короткую decision table:

- принято;
- изменено;
- отклонено;
- требует реализации позже;
- невозможно без изменения product behavior.

Любое отклонение от owner feedback объяснить до финализации.

### 2. Финальные renders

Подготовить одно согласованное направление минимум для:

1. Landing desktop light.
2. Landing desktop dark.
3. Landing mobile light/dark representative flow.
4. `/login` или auth entry.
5. AppShell + Today desktop light.
6. AppShell + Today desktop dark.
7. Active Workout mobile.
8. Nutrition diary desktop/mobile.
9. Progress/analytics.
10. Programs/wizard/exercise detail representative states.
11. Representative Mobile Web/TMA composition.
12. Loading/empty/error/validation/disabled examples для ключевых patterns.

Рендеры должны показывать не только happy-path hero screens, но и реальную плотность форм, таблиц/списков, графиков, navigation и long text.

### 3. Canonical design specification

Зафиксировать в `docs/design/` на русском языке, адаптировав имена файлов к conventions проекта:

```text
docs/design/
├── design-direction-v2.md
├── design-system-v2.md
├── component-principles-v2.md
├── responsive-and-platform-v2.md
├── motion-v2.md
└── references/
```

Минимальное содержание:

#### `design-direction-v2.md`

- brand/product thesis;
- аудитории;
- visual principles;
- premium definition;
- recognizability rules;
- approved/forbidden patterns;
- role of product imagery;
- human-made tests.

#### `design-system-v2.md`

- semantic color roles;
- light/dark behavior;
- lime usage contract;
- typography scale;
- numeric/data typography;
- spacing/grid/container;
- radii/borders/shadows;
- surface hierarchy;
- focus/error/success/warning states;
- charts/data visualization;
- icons/illustrations/images.

Не фиксировать случайные pixel values, если они ещё не проверены pilot implementation. Разделять approved intent и implementation candidate values.

#### `component-principles-v2.md`

- buttons;
- inputs/forms;
- navigation;
- cards/containers;
- tables/lists;
- dialogs/drawers/sheets;
- charts/progress;
- workout/nutrition-specific patterns;
- empty/loading/error/permission/session states;
- когда карточка действительно нужна;
- запрет локальных visual systems.

#### `responsive-and-platform-v2.md`

- desktop composition;
- Mobile Web composition;
- TMA parity;
- допустимые Telegram-specific отличия;
- safe area/keyboard/navigation;
- representative breakpoints как evidence, а не жёсткий дизайн по пяти ширинам.

#### `motion-v2.md`

- motion hierarchy;
- feedback/causality;
- duration/easing principles;
- reduced motion;
- запрещённая декоративная анимация.

### 4. Approved reference assets

После финальной сборки сохранить утверждённые reference renders в canonical project path, если это соответствует repository conventions, например:

`docs/design/references/design-v2/`

Использовать оптимизированные PNG/WebP с понятными именами. Не коммитить source prototypes, тяжёлые лишние exports или случайные промежуточные boards.

Рабочие prototypes остаются в `.artifacts/design-v2/approved/`.

### 5. Legacy transition

Зафиксировать:

- `references/landing/landing-reference-dark.png` и `landing-reference-light.png` остаются historical/legacy input;
- они не задают composition, card layout, testimonials, hero или section rhythm;
- lime + neutral palette может быть сохранена только в форме, утверждённой Design V2;
- старые визуальные указания tasks `01`, `05` и historical masters не переопределяют новую спецификацию;
- canonical logo task `07` сохраняется, если владелец отдельно не утвердил его изменение.

### 6. Проверка спецификации

Перед завершением применить `$ui-audit` к финальным renders:

- Brand Swap Test;
- Screenshot Test;
- Card Test;
- Decoration Test;
- Designer Intent Test;
- Rhythm Test;
- desktop/mobile hierarchy;
- light/dark parity;
- accessibility risks;
- implementation/performance risks.

Сделать минимум один refinement pass.

## Out of scope

- production implementation;
- migration shared components;
- Landing coding;
- TMA platform integration;
- изменение logo без отдельного owner decision;
- новая функциональность;
- полная UX-копия чужого продукта.

## STOP CONDITION

После финальных renders и tracked design documentation обязательно остановиться.

Не переходить к task `46G`.
Не изменять production UI.
Не считать направление утверждённым для реализации без явного финального ответа владельца.

Владелец должен отдельно подтвердить:

- финальные references;
- допустимость light/dark/mobile решений;
- запуск production pilot.

## Done when

- одно направление полностью отражает owner feedback;
- показаны representative Landing/Web/Mobile/TMA surfaces;
- создан единый русскоязычный source of truth в `docs/design/`;
- legacy Landing PNG корректно понижены до historical input;
- финальный UI audit пройден с refinement pass;
- production frontend не изменён;
- владелец получил checkpoint перед pilot implementation.

## Рекомендуемый commit

`docs(design): approve yfc design v2 direction`

## Процесс и отчёт

Следовать `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`. Работать только в текущей feature-ветке, не merge/deploy. Запустить только проверки документации/links/assets, если они настроены. Проверить `git diff`, создать один логический commit для approved documentation/reference assets. В финальном отчёте перечислить принятые решения, файлы, reference renders, audit/refinement, ограничения и commit hash, затем остановиться.
