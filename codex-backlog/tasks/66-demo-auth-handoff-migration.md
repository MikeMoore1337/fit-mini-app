# TASK 66. Demo Mode - auth handoff и решение по переносу введённых данных

- Фаза: **Demo conversion backend**
- Приоритет: **66/93**
- Зависит от: `13`, `65`
- Рекомендуемый reasoning: **High**
- Рекомендуемые skills: `$backend-engineer`, `$frontend-engineer`, `$qa-engineer`

## Цель

Обеспечить чистый demo -> Web/Telegram authenticated handoff без загрязнения аккаунта fixtures.

## In scope

Минимальный handoff:
1. continue/sign in;
2. существующий auth flow;
3. demo mode завершается;
4. authenticated state заменяет demo state;
5. fixtures не перезаписывают account data;
6. demo flags/state не остаются после auth/logout.

Оценить optional import только реально введённых visitor values.

Если import безопасен и малорисков:
- explicit import/discard choice;
- показать категории;
- normal domain validation;
- no silent overwrite;
- retry/idempotency safety;
- не импортировать prepared fake history/progress.

Допустимый subset: visitor-entered profile parameters, calculation inputs/results, созданная/изменённая программа.

Если import заметно расширяет риск/scope - сознательно отложить и чисто discard demo state.

Telegram continuation использует существующий canonical bot/deep-link/account-link flow.
Demo state не является Telegram identity.


## Multi-provider auth integration

Использовать canonical auth flow tasks `09-12`.

Web:

```text
Demo -> save/continue -> /login?next=<safe target> -> provider -> authenticated product
```

Не создавать Demo-specific auth system и не переносить Demo identity в OAuth identity автоматически.
Telegram continuation использует canonical TMA path.

## Out of scope

Не создавать новую auth/account-linking систему. Не импортировать fixture history/progress. Не делать implicit overwrite.

## Проверки

Tests: demo->Web auth, cleanup, logout/auth transitions, existing-user login без fake records, import/discard если реализован, Telegram continuation.

## Done when

Переход в authenticated product чистый; stale demo state отсутствует; migration реализован безопасно либо явно отложен.

## Рекомендуемый commit

`feat(demo): add authenticated handoff for demo users`

## Процесс и отчёт

Следовать корневому `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`.
Работать только в текущей выделенной feature-ветке. Не создавать и не переключать ветки,
не merge/rebase и не deploy в production без прямого указания владельца.
Не переходить к следующему task.

После изменений запустить только профильные проверки согласно `AGENTS.md`, проверить `git diff`
и создать один логический commit, если task меняет tracked files.

В финальном отчёте перечислить:
- изменения;
- ключевые файлы;
- миграции;
- реально запущенные проверки;
- ограничения;
- commit hash.
