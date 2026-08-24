# Demo Mode

Demo Mode показывает три подготовленных сценария без регистрации и без записи в пользовательские
таблицы: самостоятельная тренировка, питание и рабочий контекст тренера.

## Архитектурная граница

- публичный frontend route — `/demo`;
- публичный API — `/api/v1/demo/sessions` и дочерние endpoints текущей demo session;
- capability всегда явно равна `demo` и передаётся отдельным заголовком `X-Demo-Session`;
- demo token не является access/refresh token и не принимается authenticated endpoints;
- state хранится только в памяти backend-процесса, разделён криптографически случайным token,
  истекает через 30 минут и сбрасывается при restart процесса;
- token хранится в `sessionStorage` текущей вкладки. Он не попадает в `localStorage`, cookies,
  query string, analytics или account state;
- fixtures детерминированы, не содержат реальных снимков пользователей и имеют версию
  `demo-curated-v1`.

Текущий production deployment запускает один backend worker, поэтому process-local store даёт
предсказуемую ephemeral isolation без schema и migration. Если topology станет multi-worker,
маршрутизацию или общий ephemeral store нужно решить отдельной architecture task до увеличения
числа workers; перенос state в production user tables запрещён.

## Разрешённые действия

Demo API использует allowlist переходов:

- `self_training`: открыть тренировку, завершить подготовленный подход, завершить занятие,
  открыть Progress;
- `nutrition`: повторить подготовленный недавний продукт, открыть дневной отчёт;
- `trainer`: сохранить короткий контекстный комментарий до конца demo session;
- любой сценарий: получить текущее состояние и вернуть fixture через reset.

Неизвестные и прямые попытки вызвать приглашение, notification, provider, export, delete,
link/unlink или другое внешнее/account действие получают `403`. Demo endpoints не зависят от БД,
бота, email, notification worker или food provider.

## Срок жизни и восстановление

Reload, background/foreground и повторное открытие в той же вкладке читают то же состояние, пока
session действительна. `410 Gone` означает, что TTL истёк или backend был перезапущен; интерфейс
предлагает начать новую изолированную session. Reset возвращает исходный fixture и продлевает TTL.
Одновременные вкладки получают независимые tokens и не видят изменения друг друга.

В Mobile Web и TMA используется один component tree. `/demo` разрешён Telegram SDK loader, но не
оборачивается в `AuthProvider`/`AuthGate`: raw `initData` не отправляется в demo API и не запускает
linking. Native BackButton возвращает на landing, а не в защищённый `/app`.

## Проверка

Backend tests покрывают determinism, isolation, concurrent sessions, reset, expiry, forbidden
actions, direct production API attempts и отсутствие записей в `User`. Frontend unit tests
покрывают credential-free requests, expiry recovery и disabled/explanation state. Continuous
Playwright smoke `frontend/tests/e2e/demo-mode.spec.ts` проверяет три сценария в Mobile Web и TMA
mock, responsive geometry, reload/reset, Light/Dark и error states.

Mocked TMA и browser viewport не являются проверкой реального Telegram Android/iOS.
