# Patch existing backlog after installing UX-reset tasks

Этот файл - инструкция для точечного обновления существующих control/task docs. Не заменять owner-local task files целиком по памяти.

## 1. EXECUTION_STATUS.md

После добавления package:

- снять Task 81 с `current`, если она ещё не запускалась;
- поставить `113-development-branch-normalization` как current/new-cycle task;
- отметить 81/82/84 как pending до Task 123;
- отметить 85/110/111 как pending вне critical path, если они ещё не выполнены;
- Task 124C пометить conditional/not-required-until-124B;
- после Task 113 branch source = `dev`, production source = `master`;
- не переписывать completed history.

После каждого owner checkpoint обновлять current task явно. Lower number не является доказательством выполнения.

## 2. POST_RELEASE_PRIORITY_ORDER.md / POST_RELEASE_DEPENDENCY_GRAPH.md

Включить sequence и graph из файлов этого package. Ключевая очередь:

```text
115A -> owner approval -> 116..123 -> 81 -> 82 -> 84 -> 124A
-> owner-approved production release -> 124B -> conditional 124C
```

Удалить старое требование pre-implementation `115B` human gate, если оно уже было добавлено из предыдущей редакции package.

## 3. Task 81 - Hydration

Не заменять текущую task целиком. Добавить/уточнить:

- **dependency: Task 123**;
- выполнять после завершения нового core UX и semantic visual system;
- optional feature;
- quick `+ Вода`/hydration action на Today только в подходящем state;
- full/detail/history в Nutrition;
- не создавать новый top-level navigation section;
- Today action не должен быть permanent noise, если hydration disabled/not relevant;
- использовать semantic visual contracts Task 123, а не вводить отдельный несовместимый стиль;
- соблюдать `COMPACT_FIRST_UX_CONTRACT.md`: Today hydration = compact summary/quick action, extended controls/history не permanently expanded;
- Mobile/TMA first, обе темы.

Task 81 после этого становится обязательной частью текущего release sequence перед Task 82.

## 4. Task 82 - Sleep + Mood

Добавить/уточнить:

- **sequencing dependency: Tasks 81 и 123**;
- optional compact check-in;
- history/insights в Progress;
- Today только contextual/actionable state, не постоянная большая card;
- hidden/quiet when feature not enabled/no action;
- использовать wellbeing semantic family Task 123;
- соблюдать compact-first: check-in короткий, detail/history не разворачиваются постоянно на Today;
- не ломать Task 111 Progress hierarchy;
- если Task 111 выполняется позже, она обязана интегрировать actual Task 82 data/state, а не создавать parallel representation.

Task 82 становится обязательной частью текущего release sequence перед Task 84.

## 5. Task 84 - Reminders

Добавить/уточнить:

- **dependency: Tasks 82 и 122**;
- выполнять после 81 и 82, чтобы не переделывать reminder sources повторно;
- default-off;
- quiet hours;
- configuration under `Уведомления`/Profile hierarchy после Task 122;
- Today показывает reminder только если он действительно требует действия;
- не создавать постоянный notification feed на Today;
- не дублировать hydration/wellbeing cards отдельными reminder cards без необходимости;
- поддерживать только фактически существующие reminder sources/contracts, не выдумывать backend возможности;
- configuration sections compact summary/disclosure; не создавать длинную стену toggles по умолчанию и не делать nested accordions.

После Task 84 переходить к Task 124A.

## 6. Task 85 - Knowledge package

Изменить product placement на Public Web-first:

- dependency: Task 121;
- long-form articles/pages живут в Public Web;
- app/TMA дают contextual external handoff;
- TMA открывает public content во внешнем browser через supported Telegram API;
- не возвращать Knowledge Base как permanent app nav section;
- exercise technique остаётся in-app/contextual.

Task 85 не является обязательной для 124A, если владелец отдельно не включил её в текущий RC.

## 7. Task 110 - Custom avatar

Не заменять существующую task. Добавить acceptance из `TASK_110_AMENDMENT.md` и dependency `Task 122`.

Task 110 не является обязательной для текущего 124A gate, если владелец отдельно не включил её в RC.

## 8. Task 111 - Progress bento

Если task ещё pending:

- dependency: Task 123;
- использовать semantic variants Task 123;
- missing data != zero;
- bento не должен перегружать Progress декоративными cards;
- соблюдать compact-first: summary cards короткие и meaningful, detail charts/history по intent; не делать каждый показатель отдельной always-expanded/bento card;
- поскольку main sequence выполняет Task 82 до release gate, при последующем выполнении 111 использовать actual Sleep/Mood history/insights, а не fake/conceptual placeholder.

Task 111 не является обязательной для текущего 124A gate, если владелец отдельно не включил её в RC.

## 9. Canonical compact-first UX rules

При синхронизации control docs добавить долговечные правила из `codex-backlog/ux-reset/COMPACT_FIRST_UX_CONTRACT.md` минимум в `codex-backlog/PLAIN_LANGUAGE_UX.md` (можно ссылкой + кратким normative summary, без бессмысленного дублирования всего файла):

- primary action/current operation всегда видимы;
- secondary/detail/advanced по умолчанию compact/collapsible/contextual;
- один disclosure level максимум, затем detail screen/sheet;
- collapsed summary должен быть понятным;
- semantic wow преимущественно на meaningful compact surfaces, functional detail спокойный;
- Mobile/TMA first; disclosure accessibility обязательна.

Цель - чтобы правило продолжало действовать и для последующих owner-local/future tasks после завершения этого package.

## 10. Task 113 branch contract в глобальных rules

После фактического успешного rename в Task 113 закрепить:

- `dev` = постоянная development branch;
- `master` = production branch;
- feature/product tasks выполняются в `dev` либо task-specific branch/worktree от `dev`;
- release = reviewed/verified `dev -> master`;
- production deploy = master-only.

## 11. Human validation lifecycle

Если предыдущая версия backlog содержит Task 115B или формулировку `116+ blocked until real-user validation`, удалить это ограничение.

Новый contract:

- 115A -> owner approval;
- implementation 116..123;
- 81 -> 82 -> 84;
- 124A pre-release QA;
- owner-approved production release;
- 124B real-user validation на фактически deployed production version;
- 124C только при BLOCKER/HIGH.

Нельзя симулировать human evidence через LLM/personas.

## 12. MODEL_SELECTION / SKILL_ASSIGNMENT_MATRIX

Добавить mapping из `MODEL_SELECTION_ADDENDUM.md` и `SKILL_ASSIGNMENT_MATRIX_ADDENDUM.md` в canonical control docs при следующем backlog-maintenance pass. Не дублировать conditional skills как обязательные.
