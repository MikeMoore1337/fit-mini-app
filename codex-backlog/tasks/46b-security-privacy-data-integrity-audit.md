# TASK 46B. Security, privacy и data-integrity аудит выполненного scope

- Фаза: **Retrospective security gate**
- Приоритет: **46B/93 - выполнить после task 46A**
- Зависит от: `46A`
- Рекомендуемый reasoning: **High**
- Рекомендуемая модель: **GPT-5.6 Sol High**
- Рекомендуемые skills: `$security-engineer`, `$privacy-engineer`, `$data-engineer`, `$qa-engineer`, `$code-reviewer`, при необходимости `$solution-architect`

## Цель

Провести отдельный read-only threat-model и аудит безопасности, приватности и целостности данных для фактически реализованного продукта после tasks `00-46`.

Проверить не только наличие auth, но и реальную защиту объектов, жизненный цикл чувствительных данных, trainer/client isolation, административные границы, logging/analytics и безопасное поведение при удалении, ошибках и повторных запросах.

## Критические ограничения

- Только read-only анализ.
- Не исправлять код в этой task.
- Не повторять общий architecture audit из `46A`.
- Не реализовывать заранее scope будущих tasks `60`, `67`, `91`, `92`.
- Будущая task не оправдывает уже существующую exploitable vulnerability или риск утечки/повреждения данных.
- Не копировать секреты, токены, персональные payloads или реальные данные пользователей в отчёт.
- Не запускать destructive tests против production/staging с реальными данными.

## Threat model

До проверки определить:

- активы;
- типы пользователей и capabilities;
- trust boundaries;
- внешние входы;
- privileged actions;
- чувствительные данные;
- third-party integrations;
- основные abuse cases.

Минимальные роли и отношения:

```text
Unauthenticated
Authenticated account
Trainer capability
Trainer -> permitted client relation
Delegated Admin
Root Admin
Telegram Mini App identity
OAuth/provider identity
```

## In scope

### 1. Authentication и session lifecycle

Проверить:

- server-side validation provider callbacks/initData;
- state/nonce/PKCE и callback safety, где применимо;
- session/token storage, expiry, refresh, revocation и logout;
- open redirect;
- account linking/unlinking;
- отсутствие silent merge по email;
- Telegram identity continuity;
- отсутствие secrets/tokens в URL, client bundle, logs и errors;
- production guard для dev/test auth.

### 2. Authorization и object-level isolation

Проверить на trusted side:

- доступ пользователя только к своим profile/nutrition/workout/progress/program/measurement данным;
- trainer access только к разрешённым текущим клиентам;
- бывший/revoked/unrelated trainer-client access;
- role/capability escalation;
- admin/root boundaries;
- IDOR/BOLA через path/query/body identifiers;
- mass assignment;
- indirect access через nested resources, exports, history, notifications и media;
- list/search endpoints, которые могут раскрывать чужие объекты или metadata.

Frontend visibility не считается security boundary.

### 3. Web/API attack surface

Проверить применимые риски:

- CSRF;
- XSS и unsafe HTML/Markdown;
- SQL/command/template injection;
- SSRF;
- path traversal/file handling;
- insecure deserialization;
- CORS;
- security headers;
- rate limiting/abuse;
- oversized payloads;
- unsafe defaults;
- dependency/supply-chain findings пропорционально threat model.

Использовать OWASP ASVS как verification reference там, где он применим к фактическому стеку.

### 4. Privacy lifecycle

Составить фактический data inventory для завершённого scope:

- account/provider identities;
- profile/fitness goals;
- nutrition diary и recipes;
- workouts/programs/history;
- progress и measurements;
- trainer comments/relations;
- product analytics/events;
- logs/errors;
- exports/temp artifacts;
- external provider payloads.

Для каждой категории проверить:

```text
collection -> storage -> access -> telemetry -> third parties -> export -> deletion -> backups
```

Проверить:

- data minimization;
- purpose limitation;
- least privilege;
- response minimization;
- retention/deletion semantics;
- orphan/cascade behavior;
- account deletion impact;
- export completeness и isolation, если уже существует;
- logs/analytics/traces без лишних чувствительных payloads;
- third-party integrations получают минимум данных;
- privacy-sensitive UX без deceptive defaults.

### 5. Data integrity

Проверить:

- DB/application invariants;
- ownership constraints;
- uniqueness;
- transaction boundaries;
- lost updates;
- duplicate writes;
- replay/retry/idempotency;
- cascade/orphan semantics;
- migration/backfill safety;
- active workout offline/sync conflicts;
- timezone/user-day boundaries;
- deletion/export consistency;
- отсутствие доступа к удалённым/отозванным данным через cache, history или stale references.

### 6. Logging, analytics и error exposure

Проверить, что обычные logs/analytics/errors не содержат без необходимости:

- tokens/secrets/provider credentials;
- raw authorization headers;
- food diary contents;
- exact measurements/macros;
- trainer comments;
- real user identifiers в публичных/клиентских ошибках;
- full request/response payloads с персональными данными.

## Классификация findings

Каждый finding должен включать:

- severity;
- CWE/ASVS reference, если применимо;
- affected boundary/object;
- attack/abuse scenario или data-loss scenario;
- доказательство без раскрытия чувствительных данных;
- минимальное исправление;
- regression test expectation;
- решение:
  1. `fix in 46C`;
  2. `covered safely by future task`;
  3. `post-release hardening`;
  4. `not applicable / no issue`.

`P0/P1`, cross-user leakage, privilege escalation, secret exposure и data-loss/corruption всегда рассматриваются как кандидаты для `46C`, даже если рядом есть будущая task.

## Артефакт

Сохранить приватный отчёт в:

`.artifacts/codex-audits/46b-security-privacy-data/`

Минимальный состав:

- `threat-model.md`;
- `data-inventory.md`;
- `findings.md`;
- `coverage.md`;
- при необходимости redacted test evidence.

Не коммитить raw audit material.

## STOP CONDITION

После аудита обязательно остановиться.

Не исправлять findings.
Не переходить к task `46C`.
Не создавать commit, если tracked files не менялись.

В финальном отчёте отдельно перечислить findings, для которых требуется решение владельца до продолжения backlog.

## Done when

- построен конкретный threat model текущего продукта;
- object-level authorization и trainer/client isolation проверены на реальных routes/services;
- privacy lifecycle и data integrity рассмотрены сквозным образом;
- findings приоритизированы и отделены от будущего planned hardening;
- сформирован owner-review список для `46C`;
- `git diff` не содержит tracked changes.

## Процесс и отчёт

Следовать `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`. Работать только в текущей feature-ветке. Не создавать/переключать ветки, не merge/rebase и не deploy. Запускать только безопасные targeted checks. В финальном сообщении указать coverage, число findings по severity, blockers для продолжения, реально запущенные проверки и путь к приватным артефактам.
