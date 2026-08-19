# TASK 46B1. Консолидация findings 46A/46B и подготовка решения владельца

- Фаза: **Retrospective audit triage gate**
- Приоритет: **46B1/93 - выполнить после tasks 46A и 46B, до task 46C**
- Зависит от: `46A`, `46B`
- Рекомендуемый reasoning: **High**
- Рекомендуемая модель: **GPT-5.6 Sol High**
- Рекомендуемые skills: `$commercial-product-builder`, `$solution-architect`, `$code-reviewer`, `$security-engineer`, `$privacy-engineer`, `$data-engineer`, `$qa-engineer`

## Цель

Объединить результаты read-only аудитов `46A` и `46B` в единый доказательный реестр, перепроверить findings, удалить дубли, скорректировать severity и подготовить владельцу проекта понятный пакет решений.

Task не исправляет код и не принимает продуктовые решения вместо владельца. Её результатом должен стать точный allowlist finding IDs, который владелец сможет явно утвердить для task `46C`.

## Preconditions

Перед началом должны существовать и быть доступны:

- `.artifacts/codex-audits/46a-production-quality/`;
- `.artifacts/codex-audits/46b-security-privacy-data/`;
- итоговые сообщения tasks `46A` и `46B`, если в них есть контекст, отсутствующий в артефактах;
- текущий код, tests, конфигурация и актуальная документация проекта.

Если один из аудитов отсутствует, не завершён или не содержит доказательных findings:

1. не выдумывать недостающие выводы;
2. перечислить отсутствующие материалы;
3. остановиться без изменения tracked files.

## Критические ограничения

- Только анализ, перепроверка и triage.
- Не менять production-код, migrations, schemas, tests, styles, configuration или durable docs.
- Не исправлять findings.
- Не начинать task `46C`.
- Не создавать новые продуктовые функции.
- Не превращать task в повторный полный аудит scope `00-46`.
- Допускаются только безопасные targeted read-only проверки, необходимые для подтверждения спорного finding.
- Не запускать destructive checks и не использовать реальные персональные данные.
- Не копировать secrets, tokens, персональные payloads и exploitable details в публичные документы или финальное сообщение.
- Не считать планируемую будущую task достаточным основанием для откладывания уже существующей exploitable vulnerability, cross-user leakage или риска потери данных.

## Источники истины

Использовать в следующем порядке:

1. текущий код и фактические contracts;
2. воспроизводимые tests и безопасные targeted checks;
3. актуальные migrations/schemas/configuration;
4. актуальный `docs/`;
5. приватные отчёты `46A` и `46B`;
6. Git history - только когда без неё нельзя понять происхождение или intended invariant.

Старые task-файлы открывать точечно, только если нужно подтвердить acceptance contract или понять, покрывается ли finding конкретной будущей task.

## Порядок работы

### 1. Собрать единый реестр

Извлечь все findings из `46A` и `46B`.

Для каждого finding сохранить:

- исходный finding ID;
- источник: `46A` или `46B`;
- исходную severity;
- affected subsystem/object/boundary;
- краткое описание root cause;
- доказательство или воспроизводимый сценарий;
- реальное последствие;
- предложенное исходным аудитом действие.

Если в исходном отчёте finding не имеет стабильного ID, назначить его один раз в формате:

- `46A-<CATEGORY>-NN`;
- `46B-<CATEGORY>-NN`.

Не менять уже существующие IDs. Для переименованных или объединённых findings сохранить source mapping.

### 2. Перепроверить доказательность

Для каждого finding определить verification status:

- `confirmed`;
- `partially confirmed`;
- `not reproduced`;
- `duplicate`;
- `superseded by another root cause`;
- `needs owner/product decision`;
- `needs separate investigation`.

Finding считается подтверждённым только при наличии хотя бы одного из оснований:

- конкретный путь выполнения в коде;
- воспроизводимый безопасный сценарий;
- failing targeted test;
- доказуемое нарушение DB/API/security/privacy invariant;
- однозначно опасная конфигурация.

Не оставлять finding подтверждённым только на основании предположения, общей best practice или субъективной архитектурной оценки.

### 3. Удалить дубли и объединить root causes

Если несколько findings описывают один root cause:

- создать один canonical finding;
- сохранить все исходные IDs как aliases;
- не завышать severity из-за количества дублей;
- отдельно перечислить затронутые поверхности и regression expectations.

Не объединять findings, если для них нужны независимые исправления, разные owners или разные rollback strategies.

### 4. Нормализовать severity

Перепроверить severity с учётом:

- фактического impact;
- exploitability или вероятности сбоя;
- blast radius;
- доступности attack path;
- возможности потери, повреждения или раскрытия данных;
- существующих защитных мер;
- воспроизводимости;
- риска размножения root cause в tasks `47-93`.

Использовать уровни:

- `P0` - активный или легко реализуемый критический компромисс, массовая утечка, необратимая потеря/повреждение данных либо блокировка критического продукта;
- `P1` - серьёзная уязвимость, cross-user access, privilege escalation, существенный data-integrity/auth/core-flow дефект;
- `P2` - подтверждённый дефект качества, надёжности или защиты без немедленного критического воздействия;
- `P3` - локальное улучшение, косметика, maintainability issue без доказанного production impact.

Не повышать severity из-за эстетики архитектуры или желания провести рефакторинг.

### 5. Назначить disposition

Каждому canonical finding назначить ровно одну основную категорию:

1. `candidate for 46C`;
2. `covered safely by future task`;
3. `new standalone task required`;
4. `post-release improvement`;
5. `no action / false positive / accepted risk candidate`;
6. `needs additional investigation before decision`.

#### Обязательные кандидаты для 46C

По умолчанию включить в список кандидатов:

- все подтверждённые `P0` и `P1`;
- cross-user/client data leakage;
- IDOR/BOLA;
- privilege escalation или auth bypass;
- secret/token exposure;
- data-loss/data-corruption risk;
- unsafe migration или нарушенный critical data invariant;
- подтверждённый lost update/duplicate write критического flow;
- системный `P2`, который неизбежно будет скопирован в ближайшие tasks и имеет минимально ограниченное исправление.

Это ещё не является разрешением на исправление. Финальный allowlist утверждает владелец.

#### Правила для `covered safely by future task`

Допускается только если одновременно выполнены условия:

- указана точная task `47-93`;
- её acceptance criteria действительно закрывают root cause, а не соседнюю тему;
- до её выполнения finding не оставляет exploitable vulnerability, cross-user leakage, data-loss/corruption или критический core-flow defect;
- зафиксирована временная защита или доказано, почему риск приемлем;
- finding не потеряется при очистке `.artifacts`.

Если хотя бы одно условие не выполнено, выбрать другую disposition.

#### Правила для `new standalone task required`

Использовать, когда finding реален, но:

- не должен смешиваться с ограниченным remediation scope `46C`;
- требует отдельного discovery/migration/rollout;
- не покрывается существующими tasks;
- не является безопасным post-release improvement.

Подготовить краткий task proposal, но не создавать и не реализовывать саму task без отдельного указания владельца.

### 6. Подготовить пакет решения владельца

Сформировать отдельные списки:

#### A. Предлагаемый allowlist для 46C

Для каждого finding:

- canonical ID и aliases;
- severity;
- root cause;
- impact;
- минимальный remediation scope;
- необходимые regression tests;
- migration/compatibility risk;
- рекомендуемая очередность;
- требуется ли декомпозиция `46C.1`, `46C.2` и т.д.

#### B. Безопасно отложить

Для каждого finding:

- точная будущая task;
- почему она действительно закрывает root cause;
- почему ожидание безопасно;
- что должно быть добавлено в её acceptance criteria.

#### C. Нужна отдельная новая task

Для каждого finding:

- предлагаемое название;
- цель;
- зависимости;
- рекомендуемое место в порядке backlog;
- почему finding нельзя потерять или смешать с `46C`.

#### D. No action

Разделить:

- false positive;
- duplicate;
- already fixed;
- not applicable;
- P3/nice-to-have;
- accepted-risk candidate.

`Accepted risk` не считается утверждённым без явного решения владельца.

#### E. Нерешённые вопросы

Задать только вопросы, без ответа на которые нельзя безопасно определить disposition или scope `46C`.

## Обязательная decision matrix

Для каждого canonical finding заполнить строку:

| Canonical ID | Source IDs | Severity | Verification | Root cause | Impact | Disposition | Target task | Owner decision required | Evidence |
|---|---|---|---|---|---|---|---|---|---|

Значение `Target task` обязательно для:

- `candidate for 46C`;
- `covered safely by future task`;
- `new standalone task required`.

## Артефакты

Сохранить приватные результаты в:

`.artifacts/codex-audits/46b1-consolidated-triage/`

Минимальный состав:

- `summary.md` - краткий итог и blockers;
- `source-map.md` - соответствие исходных и canonical IDs;
- `consolidated-findings.md` - полный доказательный реестр;
- `decision-matrix.md` - итоговая классификация;
- `46c-candidate-allowlist.md` - только предложенные кандидаты для `46C`;
- `future-task-routing.md` - findings, привязанные к будущим или новым tasks;
- `owner-decision-template.md` - готовый шаблон решения владельца;
- `coverage.md` - что перепроверено и какими безопасными checks.

Не переносить raw security/privacy findings в публичный `docs/` и не коммитить audit artifacts.

## Шаблон решения владельца

В `owner-decision-template.md` подготовить редактируемый блок следующего смысла:

```text
Одобряю для task 46C только следующие canonical finding IDs:
- <ID>
- <ID>

Безопасно перенести в существующие будущие tasks:
- <ID> -> task <номер>

Оформить отдельными новыми tasks:
- <ID> -> <предлагаемое название>

Закрыть без исправления:
- <ID> -> <false positive / duplicate / not applicable / accepted risk>

Требуется дополнительное исследование:
- <ID> -> <что именно нужно подтвердить>

Все остальные findings не входят в scope 46C без нового явного подтверждения.
```

Не заполнять решение за владельца. Допускается предварительно подставить IDs в рекомендованные разделы, но владелец должен явно подтвердить итоговый текст.

## Правило перехода к 46C

Task `46C` можно запускать только после того, как владелец явно утвердил в запросе Codex:

- точный allowlist canonical finding IDs;
- решения по отложенным findings;
- необходимость декомпозиции, если она рекомендована;
- допустимые migration/compatibility изменения, если они нужны.

Отсутствие ответа владельца не означает согласие.

Если подтверждённых кандидатов для remediation нет, подготовить решение:

```text
No remediation required before Design V2.
Task 46C выполняется без изменений кода и без commit.
```

## STOP CONDITION

После подготовки owner decision package обязательно остановиться.

Не изменять production-код.
Не создавать migrations.
Не обновлять backlog tasks автоматически.
Не запускать `46C`.
Не переходить к Design V2.
Не создавать commit, если tracked files не менялись.

В финальном сообщении показать только безопасную сводку:

- число canonical findings по severity;
- число findings по disposition;
- список canonical IDs, предложенных для `46C`;
- blockers и вопросы владельцу;
- путь к приватным артефактам;
- реально выполненные checks.

Не раскрывать exploit details и чувствительные данные в финальном сообщении.

## Done when

- findings `46A` и `46B` объединены без потери source traceability;
- дубли удалены, root causes выделены;
- каждый finding перепроверен и имеет verification status;
- severity нормализована по фактическому риску;
- каждый canonical finding имеет ровно одну disposition;
- для будущих findings указан точный маршрут, поэтому они не потеряются после очистки `.artifacts`;
- подготовлен ограниченный proposed allowlist для `46C`;
- подготовлен шаблон явного решения владельца;
- production-код и tracked files не изменены;
- выполнение остановлено до owner approval.

## Процесс и отчёт

Следовать `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`. Работать только в текущей feature-ветке. Не создавать и не переключать ветки, не выполнять merge/rebase и не deploy. Использовать только безопасные targeted checks. В финальном отчёте кратко указать coverage, severity/disposition summary, proposed `46C` allowlist, owner questions и путь к приватным артефактам.
