---
name: ui-prototyper
description: >
  Explicit-only design exploration skill. Build multiple genuinely different isolated UI directions
  for comparison without changing production code, then promote only an owner-selected direction.
disable-model-invocation: true
---

# ui-prototyper

Используй только по явному запросу на варианты/эксперимент.

## Цель

Не сделать 3 оттенка одной идеи, а исследовать разные сильные ответы на одну задачу.

## Design freedom

В dedicated exploration можно полностью отойти от Design V2/V2.1.

Сохраняй только:

- sport-tech;
- mobile-first;
- lime/black/white brand core;
- product truth;
- accessibility;
- performance feasibility.

Каждый вариант должен ощущаться потенциально ship-ready, а не "crazy concept ради количества".

## Workflow

### 1. Scope

Одна meaningful surface/flow за раз.

### 2. Recon

Проверь:

- real product behavior;
- current stack;
- existing reusable components;
- current baseline;
- target user;
- mobile context.

### 3. Directions

По умолчанию 3 варианта, максимум 5.

Каждый отличается по названной оси, например:

- composition;
- density;
- interaction model;
- visual material;
- typography;
- motion;
- data representation;
- personality.

### 4. Isolation

Не менять production implementation во время exploration.

Используй:

- isolated route;
- prototype folder;
- standalone harness;
- temporary dev-only surface.

Prototype не импортируется production code.

### 5. Realistic context

- реальные product-shaped labels/data;
- working interactions;
- mobile-first viewport;
- light/dark, если это важная часть решения;
- full-size context, не только thumbnails.

### 6. Comparison

Для каждого направления укажи:

- core idea;
- what makes it different;
- strengths;
- costs/risks;
- mobile behavior;
- motion role;
- implementation complexity.

Не выбирай победителя за владельца, если не попросили рекомендацию.

### 7. Promote

Только после owner selection:

- перенеси выбранное решение через normal implementation task;
- удали/архивируй prototype по правилам task;
- обнови design source, если выбор меняет production visual system.

## Collaboration

- `$product-designer` - quality/direction;
- `$motion-design-engineer` - motion-heavy variants;
- `$landing-art-director` - Landing;
- `$frontend-engineer` - production promotion;
- `$ui-audit` - финальная rendered validation.
