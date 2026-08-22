# TASK 02A. Безопасный backport Telegram Core в production `master`

- Фаза: **Production backport / Telegram Core release**
- Статус prerequisites:
  - Telegram task `00` - **выполнена**
  - Telegram task `01` - **выполнена**
  - Telegram task `02` - **выполнена**
- Цель: выпустить результат Telegram tasks `01-02` в production `master`, не перенося весь незавершённый Platform V2.
- Source branch: `feature/yfc-platform-v2`
- Production branch: `master`
- Можно выполнять до main task `64`: **да**
- После завершения: **STOP до main task `64`**
- Рекомендуемая модель: **GPT-5.6 Sol High**
- Рекомендуемый reasoning: **High**
- Рекомендуемые skills:
  - `$telegram-engineer`
  - `$release-manager`
  - `$platform-engineer`
  - `$security-engineer`
  - `$qa-engineer`
  - `$code-reviewer`
  - `$technical-writer`
- Условные skills:
  - `$python-engineer` - если требуется адаптация bot runtime или profile sync;
  - `$backend-engineer` - только при доказанной зависимости account linking/auth;
  - `$devops-engineer` - только если такой skill реально присутствует и нужен существующему production deployment contract.
- Основная роль: `integration-release`
- Контракт роли: `.agents/roles/integration-release.md`, если роль существует в актуальном repository contract. Если такого файла нет - использовать ближайшую существующую release/integration роль, не создавая роль только ради этой task.

## Зафиксированное решение владельца

`master` соответствует production.

Владелец хочет обновить основной Telegram-бот заранее, до завершения всего `feature/yfc-platform-v2`.

Нужно перенести в production только законченный Telegram Core, сформированный результатами:

```text
Telegram 01 - единый основной бот + support/feedback
Telegram 02 - public bot UX + Bot API profile synchronization
```

Не переносить весь Platform V2.

Ботом на текущем этапе пользуется только владелец. Поэтому если task `02` уже применила к публичному боту новое имя, About, Description, avatar, commands или Menu Button, а production `master` пока не поддерживает часть нового contract, это **допустимый временный разрыв**.

Не откатывать уже применённые Bot API metadata только ради соблюдения порядка rollout, если они:

- принадлежат exact `@your_fitness_coach_bot`;
- соответствуют результату task `02`;
- не создают security/privacy риск;
- не мешают выполнению backport.

Цель этой task - как можно быстрее и безопаснее привести production runtime в соответствие уже готовому Telegram Core.

## 1. Критический принцип

Эта task является **semantic backport**, а не blind cherry-pick.

Нельзя автоматически считать, что достаточно:

```text
git cherry-pick <task-01-commit>
git cherry-pick <task-02-commit>
```

`feature/yfc-platform-v2` содержит большое количество изменений, отсутствующих в `master`. Telegram tasks `01-02` могли опираться на отдельные изменения:

- bot runtime;
- account linking;
- timezone;
- polling protection;
- Telegram login proxy-tunnel;
- auth config;
- safe logging;
- deployment configuration;
- canonical bot assets;
- shared helpers.

Поэтому сначала определить реальные зависимости, а затем перенести **минимальный законченный vertical slice**.

## 2. Отдельный worktree и backport branch

Эта task - узкое исключение из обычного правила работы только в `feature/yfc-platform-v2`.

Основной feature worktree нельзя переписывать, reset/rebase или использовать как production branch.

### Перед началом

1. Проверить текущую ветку и состояние:
   ```text
   git status
   git branch --show-current
   ```

2. Убедиться, что feature worktree не содержит незакоммиченных изменений, относящихся к Telegram `01-02`.

3. Выполнить:
   ```text
   git fetch origin
   ```

4. Зафиксировать:
   ```text
   origin/master HEAD
   feature/yfc-platform-v2 HEAD
   merge-base
   ahead/behind
   ```

Не использовать старое сохранённое число коммитов - вычислить состояние заново.

### Создать отдельную ветку от актуального production

Предпочтительно через отдельный worktree:

```text
git worktree add <safe-path> -b backport/telegram-core-01-02 origin/master
```

Если branch уже существует, не force-update её. Выбрать уникальное безопасное имя.

Целевая схема:

```text
feature/yfc-platform-v2
        |
        | read-only source
        v
backport/telegram-core-01-02
        |
        | PR
        v
master
        |
        v
production
```

Не merge/rebase всю `feature/yfc-platform-v2` в backport branch.

## 3. Определить точные source revisions

До внесения изменений определить:

- commit результата Telegram task `01`;
- commit результата Telegram task `02`;
- feature HEAD после task `02`;
- актуальный `origin/master` HEAD;
- merge-base.

Использовать:

- `git log`;
- `git show`;
- task final reports;
- commit messages;
- изменённые файлы;
- tests;
- `git diff`.

Если одна task была реализована несколькими логическими commits, перечислить все нужные commits.

Если scope невозможно надёжно восстановить только по сообщениям commits, не угадывать. Восстановить его по фактическому task contract и diff.

Task `00` была audit/research task. Её implementation переносить не требуется, кроме реально нужной durable documentation, если она является частью эксплуатации Telegram Core.

## 4. Построить dependency map

До backport классифицировать изменения.

### A. Direct Telegram Core

Переносить результат `01-02`, где фактически применимо:

- единый основной bot runtime;
- support/feedback handlers/router;
- support FSM/state;
- support deep links;
- reply relay;
- rate limiting;
- recipient allowlist;
- `/start`;
- `/app`;
- `/support`;
- `/settings`;
- `/help`;
- `/privacy`;
- backward-compatible aliases;
- canonical commands;
- canonical Menu Button;
- bot metadata/profile sync;
- bot avatar integration;
- bot tests;
- безопасный config;
- удаление/отключение отдельного support polling process;
- `.env.example`;
- deployment config, непосредственно необходимый single-bot architecture;
- durable Telegram documentation.

### B. Narrow prerequisites

Переносить только конкретные feature-изменения, без которых Telegram Core на `master`:

- не импортируется;
- не запускается;
- ломает `/start link_<token>`;
- ломает account linking;
- ломает timezone;
- ломает proxy-tunnel;
- ломает polling conflict protection;
- нарушает TLS/security/privacy;
- не проходит targeted regression.

Для каждого такого prerequisite в отчёте написать:

```text
<file/commit> required because <конкретная dependency>
```

### C. Не относящееся к Telegram `01-02`

Не переносить без доказанной необходимости:

- nutrition/food;
- workout/program features;
- Progress;
- Trainer/Admin features;
- Design V2 rollout целиком;
- Demo Mode;
- AI Coach;
- main tasks после текущего production scope;
- unrelated migrations;
- общий backlog;
- `.agents`/skills changes только потому, что они присутствуют в feature;
- широкие backend/auth refactors без прямой Telegram dependency.

Если один файл в feature содержит смешанные изменения, сделать минимальный semantic/manual port вместо копирования файла целиком.

## 5. Production compatibility важнее parity с feature

Backport должен адаптироваться к `master`.

Не превращать `master` в частично перенесённый Platform V2.

Обязательно сохранить production-инварианты:

```text
/start link_<token>
Telegram account linking
timezone
signed TMA initData auth
Telegram browser login
существующий Telegram login proxy-tunnel
TLS verification
polling lock/conflict protection
существующие production session/account semantics
```

Также сохранить существующие production notification flows, если они уже есть.

Не создавать новую notification architecture - это остаётся main task `64`.

Не менять proxy/network path без подтверждённого blocker.

Не отключать TLS verification.

Не логировать:

- bot token;
- raw `initData`;
- login secrets;
- support message body;
- attachment content;
- приватные credentials.

## 6. Database boundary

Telegram tasks `01-02` по возможности должны backport-иться без переноса unrelated Platform V2 migrations.

Если новая migration действительно обязательна:

1. доказать необходимость именно Telegram Core;
2. проверить текущую production schema `master`;
3. проверить replay/upgrade;
4. не переносить соседние feature migrations;
5. подготовить rollback/compatibility plan;
6. не менять данные вне Telegram scope.

Если functionality можно безопасно реализовать без новой production migration - предпочесть это.

## 7. Целевой production bot contract

После backport `master` должен обслуживать результат Telegram `01-02`.

### Публичный бот

```text
@your_fitness_coach_bot
```

### Один polling owner

Steady-state production:

```text
один TELEGRAM_BOT_TOKEN
один polling owner
```

Отдельный support polling process не нужен.

### Public commands

До main task `64`:

```text
start - Главное меню
app - Открыть приложение
support - Помощь и обратная связь
settings - Настройки и часовой пояс
help - Возможности и команды
privacy - Политика конфиденциальности
```

Поддержать aliases согласно фактическому результату `01-02`, например:

```text
/feedback
/cancel
/timezone
```

Не добавлять notification preferences только ради backport.

### Main menu

Ожидаемый contract task `02`:

```text
[Открыть приложение]
[Помощь и обратная связь]
[Настройки]
[Что умеет бот]
```

### Support

Сохранить фактически реализованные task `01`:

```text
/support
support_bug
support_account
support_idea
support_contact
```

и связанные:

- text/media handling;
- cancellation;
- rate limit;
- safe delivery;
- reply routing;
- controlled errors.

Не строить ticket system/CRM.

## 8. Bot API profile sync после уже выполненной task 02

Task `02` уже выполнена.

Не переисполнять её и не перепроектировать profile sync.

Использовать текущий результат как source of truth.

Проверить, что production backport включает требуемый sync mechanism для:

```text
Name
About
Description
Avatar
Commands
Menu Button
```

### Если task 02 уже применила metadata

Это допустимо.

Не откатывать metadata только потому, что production runtime временно старее.

После production rollout:

1. вызвать exact `getMe`;
2. проверить:
   ```text
   username == "your_fitness_coach_bot"
   ```
3. выполнить sync `check`;
4. если remote metadata уже соответствует canonical state - ничего не менять;
5. если есть ожидаемый безопасный diff - выполнить bounded `apply`;
6. выполнить read-back verification.

Не выполнять writes при identity mismatch.

Не вращать token.

Не отправлять массовые сообщения.

## 9. Env/config migration

Сравнить `master` и фактический target config task `01`.

Целевой steady-state должен использовать:

```text
TELEGRAM_BOT_TOKEN
```

Отдельный `SUPPORT_BOT_TOKEN` не нужен.

Использовать фактически реализованные task `01` env names для feedback.

Предпочтительный target, если именно он был реализован:

```text
TELEGRAM_FEEDBACK_ENABLED
TELEGRAM_FEEDBACK_RECIPIENT_IDS
```

Не переименовывать уже выбранный task `01` canonical config без необходимости.

### Legacy production env

Если production всё ещё содержит:

```text
SUPPORT_BOT_TOKEN
SUPPORT_BOT_ENABLED
SUPPORT_ADMIN_TELEGRAM_USER_IDS
```

не делать rollout хрупким только из-за их наличия.

Допустим короткий backward-compatible alias на один rollout, если:

- отдельный support bot не запускается;
- отдельный token не становится обязательным;
- второй polling process не возникает;
- alias помечен deprecated;
- есть ясный путь удаления.

Не выводить реальные token/recipient IDs в отчёт.

## 10. Реализовать semantic backport

В отдельной backport branch:

1. Перенести минимальный Telegram `01-02` vertical slice.
2. Адаптировать imports/config к production `master`.
3. Не тянуть unrelated feature modules.
4. Обновить только необходимые tests/docs/deploy files.
5. Сохранить conventions текущего `master`.
6. Не менять BotFather owner-only settings.
7. Не менять username.
8. Не вращать token.
9. Не менять proxy-tunnel без blocker.
10. Не переходить к Telegram task `03`.

Cherry-pick допустим только если конкретный commit:

- self-contained;
- применим поверх `master`;
- не затягивает unrelated Platform V2;
- проходит targeted review.

Иначе использовать manual/semantic port.

## 11. Targeted test suite

Запустить только релевантные проверки, но достаточно широко для production backport.

### Bot runtime

Минимум:

```text
/start
/start link_<token>
/app
/support
/settings
/help
/privacy
/feedback alias
/timezone alias
/cancel в активном support flow
unknown command
unknown /start payload
```

### Support

Проверить где применимо:

- category selection;
- text;
- photo/file;
- unsupported content;
- cancellation;
- rate limit;
- recipient delivery;
- reply routing;
- forged/invalid reply marker;
- blocked user;
- Telegram API error;
- restart/state recovery;
- no accidental forwarding outside support flow.

### Auth / integration regression

Только затронутые сценарии:

- account linking success;
- invalid/expired link token;
- linking conflict;
- timezone;
- signed TMA auth;
- Telegram browser login;
- proxy-tunnel;
- TLS verification.

### Runtime / deployment

Проверить:

- config load;
- `.env.example`;
- production-equivalent compose/config validation;
- один polling owner;
- legacy support service не запускается;
- нет duplicate polling;
- safe logs;
- restart behavior.

### Bot profile sync

Проверить:

- exact bot identity guard;
- wrong username -> no writes;
- no-op diff;
- partial diff;
- check/dry-run;
- apply только ожидаемых fields;
- read-back;
- Telegram outage/error;
- no token logs.

Не запускать полный Platform V2 suite без необходимости.

## 12. Capability parity matrix

Перед PR подготовить:

| Capability | Feature after `02` | Backport branch | Production `master` before merge |
|---|---:|---:|---:|
| One polling bot | yes | verify | record |
| Support flow | yes | verify | record |
| Linking preserved | yes | verify | record |
| Timezone preserved | yes | verify | record |
| Profile sync | yes | verify | record |
| Commands contract | yes | verify | record |
| Menu Button contract | yes | verify | record |

Не требовать parity по функциям вне Telegram `01-02`.

## 13. Independent review

После implementation выполнить отдельный independent review согласно task lifecycle.

Reviewer обязан проверить:

- случайный перенос Platform V2;
- скрытые transitive dependencies;
- auth/linking regression;
- второй polling process;
- legacy support token dependency;
- env migration;
- logging/privacy;
- token handling;
- Bot API identity guard;
- rollback;
- production scope.

Все blocker/high findings исправить и перепроверить до PR.

## 14. QA verification

После review выполнить отдельный QA pass.

Особый фокус - отличие production `master` от feature.

Минимум:

- clean config от baseline `master`;
- existing linked user;
- new `/start`;
- `/support` happy path;
- cancel/error/rate-limit;
- timezone regression;
- bot restart;
- Telegram API outage;
- wrong identity guard;
- legacy env migration;
- target env;
- no duplicate polling;
- отсутствие unrelated Platform V2 функций.

Если real Telegram client недоступен, не заявлять live verification.

## 15. Подготовить PR в `master`

После implementation + review + QA:

1. Проверить, что feature worktree не изменён task `02A`.
2. Сравнить:
   ```text
   backport branch vs origin/master
   ```
3. Убедиться, что diff содержит только Telegram Core и narrow prerequisites.
4. Push backport branch.
5. Создать PR:

```text
backport/telegram-core-01-02 -> master
```

Рекомендуемый title:

```text
feat(telegram): backport single-bot core to production
```

PR body должен содержать:

- `master` baseline SHA;
- feature source SHA;
- source commits task `01`;
- source commits task `02`;
- direct Telegram changes;
- narrow prerequisites и причины;
- явно исключённый Platform V2 scope;
- env/config migration;
- tests;
- review;
- QA;
- rollback;
- remaining BotFather-only actions.

Если GitHub credentials/tooling не позволяют создать PR:

- подготовить branch;
- push, если разрешено;
- вывести точные base/head;
- подготовить готовые title/body;
- не утверждать, что PR создан.

## 16. Production owner checkpoint

Поскольку `master` соответствует production, запуск этой task разрешает:

- анализ;
- создание отдельного worktree;
- создание backport branch;
- commits;
- tests;
- review;
- QA;
- push backport branch;
- создание PR.

Но **не является автоматическим разрешением на merge/deploy production**, если владелец явно не написал это в prompt запуска task.

Перед merge/deploy вывести один компактный checkpoint:

```text
READY FOR PRODUCTION APPROVAL

master baseline: <sha>
backport head: <sha>
PR: <url/number>
checks: <summary>
review: <summary>
QA: <summary>
config migration: <summary>
rollback: ready
current public bot metadata: <already applied / pending / partial>
```

И спросить один раз:

```text
Разрешить merge и production rollout?
```

Не создавать дополнительные owner checkpoints по обычным обратимым Bot API metadata writes.

### Если владелец заранее явно разрешил rollout

Если prompt запуска содержит эквивалент:

```text
при успешных проверках разрешаю merge/deploy в production
```

повторное подтверждение не требуется.

## 17. Production rollout после approval

После разрешения:

1. Проверить, что `origin/master` не изменился после подготовки PR.
2. Если изменился - обновить backport branch безопасно и повторить affected checks.
3. Merge PR по repository convention.
4. Не force-push `master`.
5. Зафиксировать merge SHA.
6. Использовать только существующий production deployment mechanism.
7. Не импровизировать новый deploy process.
8. Подтвердить deployed revision.
9. Проверить service health.
10. Проверить logs.
11. Проверить один polling owner.
12. Проверить отсутствие legacy support polling process.
13. Выполнить Bot API profile sync `check`.
14. Если metadata уже соответствует task `02` - no-op.
15. Если есть ожидаемый diff - bounded `apply`.
16. Выполнить read-back.

### Production smoke

Codex должен самостоятельно выполнить всё, что возможно без доступа к личной Telegram-сессии.

Если существует безопасный test chat/user - использовать его только если это уже разрешено существующим contract.

Если нет - оставить владельцу минимальный live smoke:

```text
/start
/support
/app
/settings
```

Так как ботом пока пользуется только владелец, отдельное staged user rollout не требуется.

## 18. BotFather boundary

Не просить владельца вручную повторять:

```text
Name
About
Description
Avatar
Commands
Menu Button
```

если task `02` уже применила их или profile sync может сделать это через Bot API.

BotFather-owner actions нужны только для реально недоступных безопасному Bot API настроек, например:

- Main Mini App;
- Web Login;
- platform mode toggles;
- splash/previews позже.

Если `getMe`/diagnostics показывает правильное состояние - не просить владельца ничего менять.

Не использовать личную Telegram Web-сессию владельца для автоматизации BotFather.

## 19. Rollback

До merge подготовить rollback.

### Runtime

Зафиксировать:

```text
production master SHA before merge
```

При blocker:

- использовать существующий rollback mechanism;
- либо revert backport/merge commit;
- не force-push `master`.

### Feedback emergency off

Если task `01` реализовала feature flag, использовать его для controlled degradation, например:

```text
TELEGRAM_FEEDBACK_ENABLED=false
```

При этом `/start`, linking, timezone и базовый bot runtime должны продолжать работать.

### Metadata

Поскольку task `02` уже могла применить metadata, не считать их автоматической причиной rollback.

Откатывать public metadata только если они сами вызывают реальную проблему.

Не вращать token при обычном rollback.

## 20. Документация

В `master` перенести/обновить только durable production documentation:

- single-bot architecture;
- support/feedback flow;
- recipient config;
- profile sync;
- rollout;
- rollback;
- BotFather-only boundary;
- proxy-tunnel preservation;
- отсутствие отдельного support polling/token в target architecture.

Не переносить весь Telegram backlog и весь Platform V2 backlog в production docs.

## Out of scope

Не делать:

- merge всей `feature/yfc-platform-v2` в `master`;
- backport unrelated main backlog;
- Telegram task `03`;
- main task `64`;
- Telegram task `04`;
- main task `72`;
- AI Coach;
- redesign;
- новый Telegram bot;
- смену username;
- token rotation;
- замену proxy;
- массовые сообщения;
- новый CRM/helpdesk;
- широкий DB refactor;
- force-push;
- изменение branch protection.

## Done when

Task имеет два допустимых исхода.

### Outcome A - READY_FOR_PRODUCTION_APPROVAL

- backport branch создана от актуального `origin/master`;
- Telegram capability `01-02` перенесён;
- unrelated Platform V2 не попал в diff;
- targeted tests green;
- independent review завершён;
- QA завершён;
- PR готов/создан;
- rollback готов;
- владелец получил один production checkpoint;
- STOP.

### Outcome B - PRODUCTION_ROLLOUT_COMPLETE

Только после owner approval или заранее данного явного разрешения:

- PR merged в `master`;
- production использует backport revision;
- работает один основной bot polling owner;
- support/feedback доступен;
- linking/timezone/auth regression не обнаружена;
- profile metadata соответствует task `02`;
- Bot API read-back выполнен;
- owner manual work сведён к реально необходимым BotFather-only действиям;
- rollback baseline зафиксирован;
- STOP.

## STOP CONDITION

Если production approval не дан:

```text
PR READY
-> STOP
```

Если rollout одобрен и завершён:

```text
02A COMPLETE
-> STOP
```

Не начинать main task `64` и Telegram task `03`.

## Рекомендуемый commit

Если semantic backport логично оформляется одним commit:

```text
feat(telegram): backport production bot core
```

Если безопаснее сохранить два независимых слоя:

```text
feat(telegram): backport single-bot support core
feat(telegram): backport public bot profile sync
```

Не дробить историю искусственно.

## Финальный отчёт

Указать:

- production `master` baseline SHA;
- feature source SHA;
- source commit(s) Telegram `01`;
- source commit(s) Telegram `02`;
- merge-base;
- backport branch;
- PR;
- direct Telegram changes;
- narrow prerequisites;
- excluded Platform V2 scope;
- tests;
- independent review;
- QA;
- env/config migration;
- current public bot metadata state;
- owner approval status;
- merge status;
- deployed SHA, если был rollout;
- Bot API profile sync/read-back result;
- remaining BotFather-only actions;
- rollback baseline.
