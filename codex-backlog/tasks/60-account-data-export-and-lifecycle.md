# TASK 60. Экспорт данных и жизненный цикл аккаунта

- Фаза: **Account / Privacy**
- Приоритет: **60/93**
- Зависит от: `13`, `21`, `29`, `30`, `33`, `46`, `47`
- Рекомендуемая модель: **GPT-5.6 Sol High**

## Цель

Закрыть пользовательский data lifecycle: человек должен понимать разницу между identity linking,
выходом, экспортом данных и полным удалением аккаунта.

## In scope

1. Сначала проверить current account deletion, identity unlinking, AuthIdentity,
trainer relationships и data ownership/cascade behavior.

2. Явно разделить операции:
   - logout;
   - unlink login method;
   - delete account;
   - export my data.
`unlink Google/Telegram` никогда не должен означать `delete account`.

3. Export:
   - только данные authenticated current user;
   - profile;
   - nutrition diary/custom foods owned by user;
   - programs/workouts/history;
   - progress/measurements;
   - weekly check-ins;
   - trainer relationship/history where user is data subject and export is appropriate;
   - app preferences.
Формат выбрать практичный: ZIP с JSON + CSV для табличных доменов или эквивалент.

4. Export security:
   - no arbitrary user_id parameter from client;
   - bounded/streamed generation for large history;
   - temporary artifact retention minimal and documented;
   - no secrets/tokens/provider credentials.

5. Delete account:
   - explicit high-friction confirmation;
   - clear irreversible warning;
   - revoke sessions/tokens;
   - handle AuthIdentity rows;
   - trainer/client relationships;
   - custom/private data;
   - notifications/jobs;
   - audit/security records only where retention is legitimately required by existing policy.
Не выдумывать legal retention rules — если юридически значимо, использовать актуальные официальные источники.

6. Data referential integrity:
   - deleting one user must not corrupt another user's records;
   - shared/public catalogue data must not be deleted because one user referenced it.

7. UI:
   - Profile/Account;
   - export status/download;
   - delete confirmation;
   - clear explanation of unlink vs delete.

8. AI integration later:
   tasks AI memory/conversations обязаны подключить свои данные к export/delete contract.
До AI feature эта задача должна работать для core app.

## Design V2 contract

Export status, unlink и destructive confirmations используют shared Design V2 account/form/feedback primitives. Перед UI-работой прочитать `codex-backlog/DESIGN_V2_INTEGRATION_NOTES.md` и релевантные `docs/design/*v2*`; опасное действие отделять семантикой и иерархией, не локальной несогласованной palette/card system. Проверить light/dark, desktop/mobile и loading/error/expired/confirmation states в реальном браузере.

## Out of scope

Не делать account merge.
Не делать automatic data portability import.
Не хранить export archive бессрочно.
Не показывать чужие trainer/client data.
Не добавлять photo data — фотографий в текущем release scope нет.

## Проверки

Export current user only; large history; no data; unlink last login method guard;
delete current user; trainer/client relationship; shared catalogue;
session revocation; repeated delete/export; artifact expiry; security permissions.

## Done when

Пользователь может безопасно скачать свои данные и полностью удалить аккаунт,
а auth identities и связанные данные обрабатываются предсказуемо.

## Рекомендуемый commit

`feat(account): add data export and lifecycle controls`

## Процесс

Следовать корневому `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`.

Все предыдущие tasks считаются выполненными.
Текущий код, Git history и актуальный `docs/` — source of truth по их результатам.

Не проводить повторный полный аудит репозитория.
Не перечитывать все предыдущие task-файлы.
Не читать весь `codex-backlog/masters/` без необходимости.

Если текущий task явно относится к одному master-документу,
прочитать только этот master.

Если предыдущий audit уже исследовал нужную область и результат доступен,
переиспользовать его; точечно перепроверять только факты, которые могли измениться.

Сначала прочитать текущий task, затем исследовать только релевантный набор файлов
и подсистем, необходимый для корректного выполнения задачи.

Если требуемая функциональность уже существует:
- не реализовывать её заново;
- переиспользовать текущую архитектуру;
- закрыть только реальные gaps.

Не расширять scope самостоятельно.

Если для выполнения нужен крупный architectural change вне scope:
- не начинать его автоматически;
- зафиксировать follow-up;
- выполнить безопасную часть текущего task, если возможно.

Работать только в текущей feature-ветке.

Не:
- создавать или переключать ветки;
- merge/rebase;
- deploy в production;
- переходить к следующему task.

После реализации:
1. только профильные проверки согласно `AGENTS.md`;
2. не запускать полный test suite без необходимости;
3. проверить `git diff`;
4. создать один логический commit при tracked changes;
5. краткий финальный отчёт: reused / changed / files / migrations-config / checks / follow-ups / commit hash.
