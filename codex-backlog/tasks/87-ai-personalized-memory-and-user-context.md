# TASK 87. AI Coach: долговременная персональная память

- Фаза: **AI Coach**
- Приоритет: **87/93**
- Зависит от: `60`, `82`, `84`, `85`, `86`
- Рекомендуемая модель: **GPT-5.6 Sol High**

## Цель

Помнить устойчивые предпочтения каждого пользователя отдельно, не дублируя изменяемые app facts.

## In scope

- Separate authoritative app data vs durable preferences vs conversation context.
- Durable: exercise preferences, stable training context/equipment, explanation style, optional RIR preference and other useful stable choices.
- Memory: owner, normalized key/category, value, provenance, timestamps, optional expiry.
- Explicit/high-confidence creation only; no `remember everything`.
- User controls: `Что Coach помнит обо мне?`, edit/delete one, clear all.
- Trainer personal memory = self; no client memory mixing.

## Out of scope

Не хранить mutable app facts, чужие данные, secrets, photo/image memory.

## Проверки

Create/update/dedupe/expiry/delete/clear, account isolation, trainer self, conflict with authoritative profile.

## Done when

Память полезная, структурированная, изолированная и контролируется пользователем.

## Рекомендуемый commit

`feat(ai): add controlled personalized memory`

## Процесс

Следовать корневому `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`.

Все предыдущие tasks считаются выполненными. Текущий код, Git history и актуальный `docs/` — source of truth.
Не проводить повторный полный аудит репозитория, не перечитывать все task-файлы и весь `masters/`.
Если текущий task относится к одному master — читать только его. Использовать результаты предыдущих audit вместо повторного исследования.
Исследовать только релевантные файлы и подсистемы. Если функция уже существует — переиспользовать, не дублировать.
Крупное изменение вне scope не начинать автоматически: зафиксировать follow-up.

Работать только в текущей feature-ветке. Не create/switch branch, merge/rebase, deploy и не переходить к следующему task.
После реализации: только профильные checks, `git diff`, один логический commit при tracked changes, краткий отчёт с reused/changed/files/migrations-config/checks/follow-ups/hash.

## Final release integration: account lifecycle

Durable Coach memory:
- входит в `export my data`;
- удаляется/анонимизируется согласно account deletion contract;
- clear Coach memory остаётся отдельной более узкой операцией;
- unlinking auth provider не удаляет memory/account.
