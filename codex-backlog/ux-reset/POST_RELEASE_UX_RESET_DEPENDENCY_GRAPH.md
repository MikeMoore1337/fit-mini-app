# Post-release UX Reset - dependency graph

## Critical owner-driven path

```text
113
 -> 114
 -> 115A
 -> OWNER APPROVAL
 -> 116
 -> 117
 -> 118
 -> 119
 -> 120A
 -> 120B
 -> 120C
 -> 120D
 -> 121
 -> 122
 -> 123
 -> 81  [existing owner-local task, amended]
 -> 82  [existing owner-local task, amended]
 -> 84  [existing owner-local task, amended]
 -> 124A
 -> OWNER RELEASE APPROVAL
 -> dev -> master + production deployment
 -> 124B
 -> 124C only if BLOCKER/HIGH
```

Этот package намеренно использует линейную очередь. Некоторые задачи технически можно было бы распараллелить, но пользователь выполняет backlog по одной task, а shared UI/data/contracts делают явную последовательность безопаснее и понятнее для Codex.

## Existing pending task amendments

### 81 Hydration

- dependency: Task 123;
- Today quick action + Nutrition detail/history;
- optional; no top-level navigation;
- использовать semantic visual + compact/disclosure system Task 123; extended detail не permanently expanded.

### 82 Sleep/Mood

- dependency: Task 81;
- optional compact check-in; detail/history по intent;
- history/insights in Progress;
- no permanent large Today card;
- использовать wellbeing semantic family Task 123.

### 84 Reminders

- dependency: Task 82; Task 122 already completed transitively;
- выполняется после 81/82, чтобы reminder system сразу учитывал фактически доступные current sources и не переделывался дважды;
- default-off + quiet hours;
- settings under Profile/Notifications;
- Today only actionable state; settings compact summary/disclosure, no toggle wall.

## Other pending tasks

- 85 Knowledge package -> after 121; Public Web-first.
- 110 Custom avatar -> after 122; reuse Profile/AppShell identity layout.
- 111 Progress bento -> after 123; compact meaningful summaries + detail charts/history по intent; если Task 82 уже выполнена к моменту запуска 111, интегрировать actual history/insights, а не conceptual placeholder.

Tasks 85/110/111 не являются обязательными dependencies Task 124A, если владелец не включил их в тот же release candidate.
