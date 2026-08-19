# TASK 46J. Актуализация оставшегося бэклога под Design V2 и новые production skills

- Фаза: **Backlog integration gate**
- Приоритет: **46J/93 - выполнить перед task 47**
- Зависит от: `46I`, явное одобрение владельцем Design V2 rollout
- Рекомендуемый reasoning: **Medium/High**
- Рекомендуемая модель: **GPT-5.6 Sol High**
- Рекомендуемые skills: `$commercial-product-builder`, `$solution-architect`, `$product-designer`, `$frontend-engineer`, `$mobile-engineer`, `$seo-auditor`, `$performance-engineer`, `$observability-engineer`, `$release-manager`, `$technical-writer`, `$code-reviewer`

## Цель

Точечно синхронизировать ещё не выполненные tasks `47-93` и управляющие файлы backlog с утверждённым Design V2 и актуальными production skills.

Эта task не меняет production-код и не переписывает будущий scope. Она устраняет только реальные противоречия, из-за которых будущие задачи могли бы вернуть legacy UI, старые Landing references или обойти новые quality gates.

## Критические ограничения

- Не менять application code, migrations, tests, assets продукта или `docs/design/`.
- Не выполнять задачи `47-93` заранее.
- Не пересобирать весь backlog ради стилистической унификации текста.
- Не менять бизнес-функциональность, приоритеты и зависимости без доказанной необходимости.
- Не добавлять новые продуктовые возможности.
- Не увеличивать число задач, кроме исправления явной структурной ошибки.
- Делать минимальный diff только в backlog-документации.

## Источники истины

Использовать:

1. фактический product behavior и ограничения security/privacy/SEO/accessibility;
2. утверждённые `docs/design/*v2*` и reference renders;
3. проверенную реализацию Design V2 после tasks `46G-46I`;
4. canonical logo/assets task `07`;
5. `codex-backlog/DESIGN_V2_INTEGRATION_NOTES.md`;
6. текущие tasks `47-93`, `GLOBAL_RULES.md`, `PRIORITY_ORDER.md`, `DEPENDENCY_GRAPH.md`, `MANIFEST.json`, `EXECUTION_STATUS.md` и связанные master-файлы.

Legacy Landing PNG и старые premium-redesign материалы используются только как historical context и не могут переопределять Approved Design V2.

## In scope

### 1. Общий контракт для будущих UI-задач

Для пользовательских задач `47-93` добавить только там, где это действительно нужно, требование:

- читать релевантные `docs/design/`;
- использовать существующие shared Design V2 tokens/components;
- не создавать локальную palette, typography, radii, card system или navigation language;
- не возвращать generic AI/SaaS patterns;
- сохранять единый продукт Web/Mobile Web/TMA;
- проверять существенные визуальные изменения в реальном браузере;
- не менять утверждённый дизайн без отдельного owner checkpoint.

Для backend-only задач не добавлять бессмысленные UI-указания.

### 2. Обязательная проверка конкретных будущих tasks

#### Task 72 - Telegram Mini App

Убедиться, что task остаётся platform adaptation, а не отдельным редизайном:

```text
Approved Design V2 shared UI
+ responsive mobile composition
+ Telegram platform adapter
= Telegram Mini App
```

Зафиксировать:

- те же semantic colors, typography, geometry и components;
- допустимы только platform-specific safe areas, keyboard, BackButton, haptics, auth/initData и navigation details;
- отдельный TMA-only visual system запрещён.

#### Task 73 - Landing

Убрать конфликт со старыми PNG.

Task должна реализовывать production Landing по:

- Approved Design V2;
- утверждённым Landing V2 renders;
- factual product truth;
- SEO/public IA;
- accessibility/performance constraints.

Старые `landing-reference-dark.png` и `landing-reference-light.png` оставить только как legacy input. Не считать их source of truth по hero, карточкам, testimonials, imagery, section rhythm или композиции.

Сохранить возможность грамотного использования lime + neutral/graphite palette в форме, утверждённой Design V2.

#### Task 74 - Responsive, accessibility и states

Убедиться, что task проверяет фактическую Design V2 реализацию, а не legacy system, включая:

- desktop/mobile composition;
- light/dark parity;
- keyboard/focus/contrast/touch targets;
- loading/empty/error/validation/permission/session states;
- reduced motion;
- Web/Mobile/TMA consistency.

#### Task 75 - Performance и motion

Убедиться, что task проверяет реальные Design V2 assets/effects:

- bundle/image/font loading;
- layout shift;
- main-thread work;
- animations only for hierarchy/causality/feedback;
- reduced motion;
- отсутствие тяжёлых декоративных эффектов.

#### Task 90 - AI UI

Убедиться, что AI Coach UI использует Design V2 и не создаёт отдельный generic chat/AI visual language.

#### Task 92 - Production readiness

Проверить использование актуальных skills:

- `$platform-engineer`;
- `$observability-engineer`;
- `$security-engineer`;
- `$privacy-engineer`;
- `$performance-engineer`;
- `$release-manager`;
- `$qa-engineer`.

Не дублировать закрытые findings `46A-46C`, но учитывать незакрытые owner-approved deferrals.

#### Task 93 - Final integrated audit

Добавить финальную проверку:

- Approved Design V2 across Landing/Web/Mobile/TMA;
- human-made tests;
- отсутствие legacy visual fragments;
- закрытие или документированное решение findings `46A-46C`;
- production readiness/observability/release evidence.

### 3. Управляющие файлы backlog

Точечно обновить, если они перечисляют строгий порядок или зависимости:

- `PRIORITY_ORDER.md`;
- `DEPENDENCY_GRAPH.md`;
- `MANIFEST.json`;
- `EXECUTION_STATUS.md`;
- `00_START_HERE.md`;
- `COMPLETION_CHECKLIST.md`;
- релевантные master/integration notes.

Зафиксировать порядок:

```text
46 -> 46A -> 46B -> 46C -> 46D -> 46E
   -> owner choice
   -> 46F
   -> owner approval
   -> 46G
   -> owner manual test
   -> 46H
   -> owner approval
   -> 46I -> 46J -> 47
```

Исходные номера `47-93` не перенумеровывать.

### 4. Конфликт-анализ

Для каждого изменённого будущего task-файла кратко зафиксировать:

- какой конфликт найден;
- почему существующий текст мог привести к неверной реализации;
- какое минимальное изменение внесено;
- изменился ли functional scope - ожидаемый ответ обычно `нет`.

## Out of scope

- реализация UI или backend;
- повторный аудит продукта;
- новые renders;
- изменение утверждённого Design V2;
- изменение logo;
- полный редакторский rewrite всех 47 задач;
- перенос будущих задач на другие номера без необходимости.

## Проверки

- проверить все ссылки на task IDs и файлы;
- проверить JSON validity `MANIFEST.json`, если он изменён;
- проверить отсутствие циклических/невозможных зависимостей;
- выполнить поиск legacy формулировок, где старые Landing PNG названы утверждённым source of truth;
- проверить `git diff`, чтобы он содержал только backlog-документацию.

## STOP CONDITION

После синхронизации backlog обязательно остановиться.

Не начинать task `47`.
Не менять product code.
Не выполнять новый дизайн или функциональность.

## Done when

- tasks `47-93` не противоречат Approved Design V2 и новым quality gates;
- task `72` остаётся общей TMA-адаптацией;
- task `73` больше не воспроизводит legacy AI/SaaS Landing references;
- tasks `74`, `75`, `90`, `92`, `93` используют актуальные критерии;
- управляющие файлы отражают tasks `46A-46J`;
- исходный functional scope будущего backlog сохранён;
- diff ограничен backlog-документацией.

## Рекомендуемый commit

`docs(backlog): align remaining tasks with design v2`

## Процесс и отчёт

Следовать `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`. Работать только в текущей feature-ветке, не merge/deploy. Проверить ссылки, зависимости, JSON и `git diff`, затем создать один логический commit. В финальном отчёте перечислить изменённые backlog-файлы, устранённые конфликты, проверки и commit hash. После этого остановиться.
