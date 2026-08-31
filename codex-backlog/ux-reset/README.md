# YFC Post-release UX Reset - task package

Этот пакет рассчитан на существующий repository `MikeMoore1337/fit-mini-app`. Новый repository **не нужен**.

## Что изменено в этой редакции

Добавлен глобальный **compact-first / progressive-disclosure contract**: интерфейс не должен быть длинным полотном из permanently expanded sections. Primary action/current operation остаются видимыми, secondary/detail/advanced information сворачивается либо уходит в detail screen/sheet. Compact summary/action cards становятся одним из основных носителей visual wow. Правило применяется по всему UX-reset и через amendments к Tasks 81/82/84/111.

Real-user validation перенесена **после production release**. Причина: текущая инфраструктура не даёт реалистично проверить Web/TMA внешними пользователями на отдельном dev/staging environment.

Поэтому lifecycle теперь такой:

1. Task 115A - owner-reviewed UX/IA/prototype direction;
2. Tasks 116-123 - implementation;
3. existing Tasks 81 -> 82 -> 84 - интеграция hydration/wellbeing/reminders уже в новую IA;
4. Task 124A - pre-release integrated QA;
5. owner-approved `dev -> master` production release;
6. Task 124B - реальные пользователи проверяют фактически deployed production version;
7. Task 124C - только если 124B нашла `BLOCKER/HIGH`.

## Что внутри

Исполняемые new-cycle tasks находятся в `codex-backlog/tasks/`:

1. `113-development-branch-normalization.md`
2. `114-nutrition-search-barcode-production-regression.md`
3. `115A-post-release-ux-audit-ia-prototype.md`
4. `116-core-navigation-today-quick-start.md`
5. `117-first-run-without-mandatory-onboarding.md`
6. `118-simple-training-program-flow.md`
7. `119-type-aware-workout-logging.md`
8. `120A-exercise-catalog-coverage-taxonomy-media-audit.md`
9. `120B-exercise-library-upper-body-machine-expansion.md`
10. `120C-exercise-library-lower-body-machine-expansion.md`
11. `120D-exercise-library-remaining-coverage-search-hardening.md`
12. `121-knowledge-base-main-ia-removal-public-web-handoff.md`
13. `122-profile-settings-simplification.md`
14. `123-semantic-card-visual-system.md`
15. `124A-pre-release-integrated-ux-qa-gate.md`
16. `124B-production-real-user-usability-validation.md`
17. `124C-post-validation-remediation.md` - conditional

Control-файл `codex-backlog/ux-reset/COMPACT_FIRST_UX_CONTRACT.md` является обязательным UX contract для этого цикла и должен быть перенесён в canonical `PLAIN_LANGUAGE_UX.md` при синхронизации backlog.

Tasks 81/82/84/85/110/111 уже существуют owner-local и поэтому намеренно **не дублируются** в архиве. Их placement/dependencies меняются через `codex-backlog/ux-reset/PATCH_EXISTING_BACKLOG.md`; Public Web-first contract Task 85 дополнительно закреплён в `TASK_85_AMENDMENT.md`.

## Рекомендуемый запуск Codex

Для первой task:

```text
Выполни `codex-backlog/tasks/113-development-branch-normalization.md`.
Соблюдай `AGENTS.md`, `codex-backlog/GLOBAL_RULES.md` и полный task lifecycle.
Ориентируйся на `codex-backlog/EXECUTION_STATUS.md` как на источник фактического статуса существующих tasks.
Не переходи к следующей task.
```

После Task 113 все новые product tasks выполняются из `dev` либо task-specific branch/worktree от `dev` по repository rules. Production source остаётся `master`.

## Lower-number pending tasks

Номера 81/82/84/85/110/111 могут оставаться pending, даже когда выполняется 113+. Их меньший номер не означает, что они автоматически выполнены.

Для этого цикла обязательна последовательность:

```text
... -> 122 -> 123 -> 81 -> 82 -> 84 -> 124A
```

Tasks 85/110/111 не входят в critical path этого UX-reset release, если владелец отдельно не включит их в тот же RC.

## Hard gates

- 115A требует явного owner approval target IA/prototype/spec, включая compactness/disclosure hierarchy.
- После 115A сразу начинается implementation; pre-release human gate отсутствует.
- 81/82/84 выполняются только после 123 в указанном порядке.
- 124A не деплоит production без явного owner release decision.
- 124B стартует только после реального production deployment и проверки deployed version.
- 124B нельзя закрыть без реальных human sessions.
- 124C выполняется только при `BLOCKER/HIGH` после 124B.
