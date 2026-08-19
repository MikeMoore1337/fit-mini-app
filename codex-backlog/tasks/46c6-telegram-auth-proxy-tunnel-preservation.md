# TASK 46C.6. Сохранение proxy-tunnel для Telegram login

- Фаза: **Retrospective remediation gate / Auth infrastructure**
- Приоритет: **46C.6/93 - выполнить после task 46C.5 и до task 46D**
- Зависит от: `46C.5`
- Основание: **явно подтверждённый владельцем production-инвариант**
- Рекомендуемый reasoning: **High**
- Рекомендуемая модель: **GPT-5.6 Sol High**
- Рекомендуемые skills: `$solution-architect`, `$security-engineer`, `$platform-engineer`, `$backend-engineer`, `$python-engineer`, `$qa-engineer`, `$code-reviewer`

## Контекст

В текущей рабочей архитектуре вход через Telegram зависит от существующего **proxy-tunnel / proxy network path**. Этот механизм уже обеспечивает доступность Telegram login в целевом окружении и должен быть сохранён при дальнейших изменениях приложения.

Это не задача на создание нового proxy, VPN или второго Telegram auth flow. Сначала необходимо найти фактическую реализацию в актуальном коде, конфигурации, deployment-файлах и документации. Нельзя заранее предполагать конкретную технологию туннеля, адрес, провайдера или набор env-переменных.

## Цель

Зафиксировать существующий Telegram proxy-tunnel как обязательный архитектурный инвариант, проверить его фактическое использование и добавить достаточную regression-защиту, чтобы последующие задачи не могли случайно удалить, обойти или небезопасно заменить рабочий сетевой путь Telegram login.

## Важная граница

Не считать, что каждый Telegram flow обязательно выполняет outbound-запрос через tunnel.

Нужно отдельно определить фактическое поведение для:

- Telegram browser login/OAuth/OIDC;
- Telegram account linking;
- bot/deep-link flow, если он участвует во входе;
- Telegram Mini App signed `initData`;
- обмена token/profile/provider metadata;
- иных Telegram API вызовов, связанных с authentication.

Если signed `initData` валидируется локально и не требует outbound Telegram request, не проксировать его искусственно. Tunnel должен применяться только к тем операциям, которым он реально необходим в текущей архитектуре.

## In scope

### 1. Discovery текущей реализации

До любых изменений определить и зафиксировать:

- какие Telegram login/linking flows реально используют tunnel;
- где создаётся и настраивается Telegram HTTP/provider client;
- какие env/config параметры управляют proxy/network path;
- является ли proxy Telegram-specific или частью общего OAuth network layer;
- какие timeout, retry, IPv4/IPv6 и TLS параметры с ним связаны;
- где tunnel описан в deploy/runtime configuration;
- как система ведёт себя при его недоступности;
- существуют ли прямые Telegram outbound calls в обход canonical client;
- какие тесты уже защищают этот путь.

Текущий код, Git history, актуальный `docs/` и deployment configuration являются source of truth. Raw diagnostic artifacts хранить только в `.artifacts/`.

### 2. Сохранение существующего network path

После discovery закрыть только реальные gaps.

Требования:

- не удалять и не заменять рабочий tunnel без отдельного owner decision;
- не добавлять прямые Telegram HTTP-вызовы в обход canonical network/provider abstraction;
- не создавать второй Telegram auth adapter только ради proxy;
- сохранить текущие identity, session и account-linking semantics;
- не создавать `AuthIdentity` или session до подтверждённого provider result;
- не отключать TLS verification;
- не отправлять proxy URL, credentials или другие server secrets во frontend;
- не менять Google, Яндекс, VK или другие provider paths без доказанной связи с shared network layer;
- сохранить backward compatibility действующих production env/config names либо предоставить безопасный миграционный путь.

Если текущая реализация уже корректна, не переписывать её. Добавить только недостающую документацию, проверки и минимальные safeguards.

### 3. Failure behavior

При недоступном tunnel Telegram login должен завершаться контролируемой provider/network ошибкой.

Обязательные свойства:

- нет частично созданной авторизации;
- нет silent fallback на неподтверждённый прямой путь;
- пользователь не видит internal proxy URL, credentials или raw provider error;
- повторный вход возможен после восстановления network path;
- TMA `initData` flow не ломается из-за unrelated outbound provider failure, если он от него фактически не зависит;
- core-приложение и другие login providers не становятся недоступными без архитектурной причины.

Прямой fallback допустим только если он уже является подтверждённой частью текущего production contract и реально работает в целевом окружении. Не добавлять его предположительно.

### 4. Конфигурация и secrets

Зафиксировать server-only contract для найденной реализации:

- enable/disable semantics;
- источник proxy/tunnel configuration;
- timeout/network settings;
- ожидаемое поведение при отсутствующей или некорректной конфигурации;
- redaction proxy credentials и provider secrets;
- local/test/production expectations.

Не коммитить реальные proxy URL с credentials, tokens, private certificates или иные secrets.

### 5. Regression coverage

Добавить профильные тесты по фактической архитектуре, включая где применимо:

- configured tunnel передаётся в canonical Telegram outbound client;
- Telegram login/linking не создаёт отдельный direct client в обход tunnel;
- tunnel timeout/connectivity failure даёт контролируемый auth failure;
- success сохраняет существующие account/session/linking semantics;
- TMA valid/invalid/stale `initData` regression не ломается;
- TLS verification остаётся включённой;
- proxy credentials не попадают в public config, frontend bundle, errors и logs;
- другие providers не начинают использовать Telegram-specific tunnel без основания;
- CI не зависит от живого внешнего tunnel.

Live smoke через реальный Telegram/tunnel выполнять только если это безопасно, доступно и не требует раскрытия secrets. При невозможности прямо указать ограничение и не заявлять production connectivity как проверенную.

### 6. Минимальная эксплуатационная диагностика

Переиспользовать текущий logging/observability contract.

Допустимо добавить:

- безопасный provider/network error code;
- distinction timeout/connectivity/tunnel unavailable, если оно не раскрывает инфраструктуру;
- request/correlation ID;
- bounded operational context без Telegram payloads, tokens, exact user/chat IDs и proxy credentials.

Не превращать задачу в общую observability-платформу - расширенное operational hardening остаётся в task `92`.

### 7. Документация

Обновить актуальную документацию в `docs/` на русском языке и зафиксировать:

- что Telegram login зависит от существующего proxy-tunnel/network path;
- какие конкретные flows от него зависят;
- какие server-only настройки обязательны;
- как проверить конфигурацию и безопасный failure;
- как диагностировать проблему без публикации secrets;
- что tunnel нельзя удалять или обходить при auth/provider refactoring без отдельного решения и regression-проверки.

Не копировать реальные secrets и приватные адреса в документацию.

## Интеграция в последовательность backlog

При включении задачи в полный backlog зафиксировать порядок:

```text
46C.5
  -> 46C.6 Telegram auth proxy-tunnel preservation
  -> 46D Design V2 baseline audit
```

Также обновить coordination contract task `46C`, `PRIORITY_ORDER.md`, `DEPENDENCY_GRAPH.md`, `MODEL_SELECTION.md`, `MANIFEST.json` и зависимость task `46D`, не меняя результаты уже выполненных tasks `00-46`, `46A`, `46B` и `46B1`.

## Out of scope

- создание нового VPN/proxy service;
- смена провайдера tunnel без необходимости;
- переработка Telegram login UX;
- новая auth-система;
- account merge;
- изменение Root/Admin/Trainer permission model;
- Telegram-only frontend;
- production deploy;
- отключение TLS verification;
- общий рефакторинг всех OAuth providers;
- полная observability/backup/deploy работа task `92`.

## Проверки

Минимум:

1. Подтвердить фактический текущий network path и связанные flows.
2. Проверить config/env/deploy path без раскрытия secrets.
3. Запустить targeted backend auth/provider/network tests.
4. Проверить mocked Telegram browser login/linking success и tunnel failure.
5. Проверить TMA signed `initData` regression.
6. Проверить отсутствие direct Telegram outbound path в обход canonical client.
7. Проверить secret redaction и отсутствие proxy config в public frontend config.
8. Проверить `git diff` и отсутствие unrelated auth/provider redesign.

## Done when

- фактическая реализация существующего Telegram proxy-tunnel найдена и документирована;
- все зависящие от него login/linking flows используют canonical path;
- прямой обход tunnel отсутствует либо явно обоснован фактической архитектурой;
- regression tests защищают network path и auth semantics;
- failure безопасен и диагностируем;
- TMA `initData` и другие providers не сломаны;
- secrets не раскрываются;
- рабочий Telegram login не заменён неподтверждённой схемой.

## STOP CONDITION

После закрытия proxy-tunnel invariant, targeted review, `git diff` и отдельного commit остановиться. Не начинать task `46D`.

## Рекомендуемый commit

`fix(auth): preserve telegram proxy tunnel`

## Процесс и отчёт

Следовать `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`.

Работать только в текущей feature-ветке. Не создавать и не переключать ветки, не merge/rebase и не deploy. Не переходить к следующей task.

После изменений:

1. запустить только профильные проверки;
2. проверить `git diff`;
3. создать один логический commit при tracked changes;
4. в финальном отчёте указать:
   - как фактически устроен найденный tunnel;
   - какие flows от него зависят;
   - какие env/config задействованы без значений secrets;
   - что переиспользовано и что изменено;
   - какие проверки реально выполнены;
   - выполнялся ли live smoke;
   - ограничения среды;
   - commit hash.
