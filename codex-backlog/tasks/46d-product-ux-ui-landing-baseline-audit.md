# TASK 46D. Product UX/UI и Landing baseline-аудит перед Design V2

- Фаза: **Design V2 discovery**
- Приоритет: **46D/93 - выполнить после технического gate 46C**
- Зависит от: `46C` или подтверждение `no remediation required`
- Рекомендуемый reasoning: **High**
- Рекомендуемая модель: **GPT-5.6 Sol High**
- Рекомендуемые skills: `$product-discovery`, `$product-designer`, `$ui-audit`, `$frontend-engineer`, `$qa-engineer`

## Цель

Провести независимый read-only аудит фактического пользовательского опыта и визуального качества продукта после tasks `00-46` до разработки Design V2.

Нужно понять не только что выглядит слабо, но и:

- какие пользовательские сценарии содержат лишний friction;
- какие решения стоит сохранить;
- где UI выглядит шаблонным, AI-generated или слишком похожим на generic SaaS;
- почему текущий Landing не создаёт ощущение зрелого коммерческого продукта;
- какие ограничения реального продукта должен учитывать новый art direction.

## Критические ограничения

- Не менять production frontend, design tokens, components, routes, content или assets.
- Не создавать Design V2 в этой task.
- Не исправлять найденные UI/UX defects.
- Не считать старые Landing PNG целевым source of truth.
- Не проводить новый технический/security audit, уже закрытый tasks `46A-46C`.
- Не придумывать функции, метрики, отзывы, тарифы или обещания.

## Обязательные источники

Изучить:

- фактический render текущего Web-приложения;
- representative Mobile Web;
- текущий TMA render/platform adapter, если воспроизводим;
- текущий public Landing и `/login`;
- реальные user/trainer flows, доступные после task `46`;
- canonical logo/assets task `07`;
- текущие tokens/components/theme implementation;
- `codex-backlog/DESIGN_V2_INTEGRATION_NOTES.md`;
- `codex-backlog/LANDING_REFERENCE_NOTES.md`;
- `references/landing/landing-reference-dark.png` и `landing-reference-light.png` только как legacy input;
- актуальный `docs/` по UX/design/product behavior.

## Legacy Landing references

Старые light/dark PNG не являются утверждённой композицией Design V2.

Разрешено учитывать из них только потенциально удачные элементы, если audit это подтверждает:

- lime как фирменный акцент;
- graphite/dark neutral base;
- чистую light theme;
- идею показывать реальный Web + mobile product;
- единый бренд для самостоятельного пользователя и тренера.

Нельзя автоматически наследовать:

- hero `text left + laptop/phone right`;
- длинную последовательность одинаковых rounded cards;
- feature-icon grids;
- synthetic testimonials/avatars/ratings;
- однообразный ритм секций;
- excessive centered headings;
- stock/AI fitness people;
- композицию, которую можно без изменений применить к любому SaaS.

## In scope

### 1. Critical journeys

Проверить фактический UX минимум для:

```text
Landing -> login/demo
Login -> onboarding -> Today
Today -> program/workout
Active workout -> set complete -> recovery -> finish
Nutrition -> add/edit/search/copy
Programs -> selection wizard -> preview/start
Progress -> measurements/trends
Exercise catalog -> guide/detail
Mobile Web navigation
Representative TMA launch/navigation, если доступно
```

Для каждого потока оценить:

- time-to-value;
- unnecessary steps;
- cognitive load;
- clarity of labels/CTA;
- feedback после действий;
- recovery/retry/cancel;
- repeated-use friction;
- trust и ощущение контроля;
- beginner-friendly terminology;
- consistency Web/Mobile/TMA.

### 2. Visual audit фактического render

Проверить в реальном браузере минимум:

- 1440;
- 1280;
- 768;
- 390;
- 360;
- light/dark;
- populated/empty/loading/error/validation/disabled;
- hover/focus/keyboard;
- reduced motion, где применимо.

Оценить:

- art direction;
- typography;
- grid/spacing;
- density;
- hierarchy;
- proportions;
- cards/surfaces;
- radii/borders/shadows;
- data visualization;
- navigation;
- mobile composition;
- visual continuity between public/auth/app surfaces;
- recognizability of Your Fitness Coach.

### 3. Human-made design tests

Провести и зафиксировать:

#### Brand Swap Test

Если заменить название и логотип, сможет ли тот же UI естественно принадлежать любому Health/Finance/Productivity SaaS?

#### Screenshot Test

Выглядит ли screenshot как очередной Tailwind/shadcn/AI dashboard?

#### Card Test

Можно ли убрать половину контейнеров и карточек без потери структуры?

#### Decoration Test

Есть ли визуальные элементы без роли в hierarchy, brand или interaction?

#### Designer Intent Test

Можно ли объяснить размеры, spacing, color, radius, layout и motion конкретной продуктовой причиной?

#### Rhythm Test

Есть ли controlled variation of scale/density/composition или каждая секция построена одинаково?

### 4. Current strengths

Обязательно отделить то, что следует сохранить:

- работающие IA/patterns;
- понятные flows;
- удачные компоненты;
- фирменные цвета;
- logo/brand assets;
- сильные data visualizations;
- хорошие mobile решения;
- доступные interaction patterns.

Аудит не должен оправдывать тотальное изменение всего подряд.

### 5. Design constraints для следующей task

Подготовить конкретный brief:

- аудитории и их primary jobs;
- ключевой product promise;
- обязательные surfaces;
- поддерживаемые темы/platforms;
- реальная информационная плотность;
- допустимые/недопустимые изменения;
- brand assets;
- content/product truth constraints;
- SEO/accessibility/performance constraints;
- legacy patterns, которые нельзя переносить в Design V2.

## Артефакты

Сохранить в:

`.artifacts/codex-audits/46d-design-v2-baseline/`

Минимальный состав:

- `ux-journeys.md`;
- `visual-audit.md`;
- `keep-change-remove.md`;
- `design-v2-brief.md`;
- `screenshots/`;
- `coverage.md`.

## STOP CONDITION

После предоставления аудита обязательно остановиться.

Не создавать визуальные направления.
Не менять production-код.
Не переходить к task `46E`.
Не создавать commit, если tracked files не менялись.

## Done when

- критические journeys проверены на фактическом продукте;
- текущий UI и Landing оценены по human-made/premium критериям;
- старые Landing references корректно переведены в legacy status;
- сильные решения отделены от проблем;
- подготовлен исполнимый Design V2 brief без преждевременного редизайна;
- `git diff` не содержит tracked changes.

## Процесс и отчёт

Следовать `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`. Использовать Playwright MCP в Codex IDE и фактические browser/e2e scripts проекта. Не использовать unsupported In-app Browser. В финальном сообщении кратко указать главные UX/visual findings, что сохранить, главные ограничения для Design V2, реально проверенные viewports/states и путь к артефактам.
