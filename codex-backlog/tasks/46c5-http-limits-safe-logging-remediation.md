# TASK 46C.5. HTTP limits and safe logging remediation

- Фаза: **Retrospective remediation gate**
- Приоритет: **46C.5/93 — последняя implementation task umbrella 46C**
- Зависит от: `46C.4`
- Canonical findings: `F46B-05`, `F46B-06`
- Дополнительный approved regression: stale `Cache-Control` test expectation
- Рекомендуемый reasoning: **High**
- Рекомендуемая модель: **GPT-5.6 Sol High**
- Рекомендуемые skills: `$solution-architect`, `$security-engineer`, `$privacy-engineer`, `$platform-engineer`, `$backend-engineer`, `$python-engineer`, `$qa-engineer`, `$code-reviewer`

## Цель

Ограничить oversized request bodies одинаково на edge/ASGI boundary и исключить произвольные
personal values/identifiers из ordinary production logs, сохранив диагностируемость через safe
codes и request ID.

## Owner-approved contract

- Default limit для JSON/form: `1 MiB`.
- Auth endpoints limit: `64 KiB`.
- Future upload/import endpoints получают только explicit reviewed exceptions.
- Edge и ASGI возвращают согласованный `413` до полного parsing oversized body.
- `Cache-Control: no-store, private` — правильное production behavior; заголовок не ослаблять.

## Scope

1. Настроить `1 MiB` default body limit на production edge и ASGI streaming boundary.
2. Применить `64 KiB` к auth JSON/form endpoints, включая provider callbacks только в пределах их
   фактического безопасного payload contract.
3. Не buffer oversized body целиком до решения; response — stable generic `413` без echo payload.
4. Одинаково обработать known/unknown/chunked bodies насколько позволяет current stack; malformed
   length не должен обходить application boundary.
5. Не добавлять broad upload exception. Любая будущая exception требует отдельной task, endpoint,
   documented max size, streaming/storage/threat review и tests.
6. Last-resort production logging не сериализует raw traceback, exception message, SQL params,
   food/note/measurement text, tokens или exact user/chat identifiers.
7. Сохранить allowlisted exception type/diagnostic code, request ID и bounded safe operational fields.
8. Псевдонимизировать/маскировать identifiers там, где correlation действительно нужна.
9. Исправить только stale test assertion, ожидающий exact `no-store`: тест должен принимать/ожидать
   production contract `no-store, private`. Не менять middleware на более слабый header.

## Configuration и compatibility

- DB migration отсутствует.
- Edge и app limits должны быть заданы из одного documented contract и не расходиться silently.
- Проверить все существующие legitimate JSON/form payloads; текущие auth, Telegram initData и OAuth
  callbacks должны помещаться в `64 KiB`.
- Log change не должен лишить оператора request correlation и безопасного error classification.

## Targeted regression

- Body на/под каждым limit проходит; превышение на один byte получает `413` на edge и ASGI.
- Unknown fields, chunked/streaming requests и invalid content length не обходят limit.
- Valid Telegram/OAuth/dev-auth test payloads не ломаются.
- Synthetic exception с secret/URL/name/note/measurement/chat ID не оставляет marker.
- Safe exception type/code и request ID сохраняются.
- Worker не пишет exact chat ID.
- Private/authenticated responses сохраняют `Cache-Control: no-store, private`; stale assertion
  обновлён, header не ослаблен.

Запустить targeted middleware/auth/security/logging/worker tests, edge config validation и только
релевантные compose/config checks. Production deploy и полный suite не запускать.

## Documentation

Обновить operations/security documentation: limits, exception review procedure и safe logging
fields. Retention/access/backup lifecycle `F46B-08` не закрывать здесь — он закреплён за task 92.

## STOP CONDITION

После закрытия `F46B-05`, `F46B-06`, cache assertion regression, targeted review, `git diff` и
отдельного commit остановиться. Не начинать `46D`.

## Рекомендуемый commit

`fix(security): bound request bodies and sanitize error logs`

## Процесс и отчёт

Следовать `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`. Указать edge/app config, cache contract,
реально выполненные checks, limitations и commit hash.
