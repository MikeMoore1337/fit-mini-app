# Demo Mode

Demo Mode показывает в Web и Mobile Web три подготовленных сценария без регистрации и без записи в
пользовательские таблицы: самостоятельную тренировку, питание и рабочий контекст тренера. Сценарии
работают внутри ограниченного production `AppShell`, поэтому посетитель видит те же навигацию,
семантические токены и базовые разделы, что и в обычном кабинете.

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

Демо доступно только как браузерный продуктовый маршрут. Если `/demo` открыт как подписанный Telegram
Mini App launch, frontend до авторизации удаляет оставшиеся demo credentials и переводит запуск в
обычный `/app`. Demo UI, demo navigation и demo mutations в TMA не открываются.

## Ограниченный кабинет

Allowlist кабинета включает `Сегодня`, `Питание`, `Прогресс` и подготовленный контекст клиента для
trainer preset. Разделы читают один связный snapshot: подтверждённая тренировка меняет факты
прогресса, добавленный продукт меняет дневной итог и его отражение в прогрессе, а комментарий тренера
существует только до конца текущей demo session. Остальные разделы production-кабинета в demo
navigation отсутствуют.

Постоянная граница `Демо` объясняет изоляцию, даёт reset и выход. Conversion CTA появляется только
после meaningful action. Его текст не обещает продолжение или перенос подготовленного результата:
он отделяет увиденную механику продукта от будущей настройки собственного профиля. Перед переходом
к login удаляются все demo credentials; регистрация и вход всегда продолжаются с чистого onboarding
без переноса fixture state.

На desktop подготовленные сценарии не сжимаются в узкой боковой навигации. Однострочный
компактный переключатель находится в верхней границе кабинета: постоянная подпись
`Демо-сценарий:` отделена от select шириной `120px`, а его значения сокращены до
`Для себя|Питание|Тренер`. Select использует единственную системную стрелку раскрытия, оставляет
под неё отдельную область и не меняет ширину при выборе сценария. На ширинах `900–1099px`
сообщение занимает первую строку, а переключатель и действия — выровненную вторую. На Mobile
Web пункт нижней навигации называется `Сценарии`, а не абстрактное `Ещё`, а panel сохраняет полные
названия путей. Технические слова `fixture`, `snapshot` и названия внутренних контрактов не выводятся
посетителю: подготовленные данные называются демонстрационным примером.

Текущий production deployment сохраняет ровно одного активного backend worker, поэтому process-local store даёт
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

В Web и Mobile Web используется один component tree. `/demo` не оборачивается в
`AuthProvider`/`AuthGate`, а raw Telegram `initData` никогда не отправляется в demo API. Подписанный
TMA launch является только безопасной границей перехода в обычный авторизованный продукт.

## Проверка

Backend tests покрывают determinism, isolation, concurrent sessions, связность cabinet snapshot,
reset, expiry, forbidden actions, direct production API attempts и отсутствие записей в `User`.
Frontend unit tests покрывают credential-free requests, route allowlist, expiry recovery и
disabled/explanation state. Continuous Playwright smoke `frontend/tests/e2e/demo-mode.spec.ts`
проверяет три сценария в Mobile Web, responsive geometry, keyboard, reload/reset, Light/Dark и error
states. Отдельная negative-проверка подтверждает, что подписанный TMA launch не открывает demo UI и
не вызывает demo API.

Browser viewport не является проверкой реального устройства; само демо в Telegram Android/iOS не
поддерживается по продуктовому решению.
