# TASK 01. Единый основной бот, помощь и обратная связь

- Фаза: **Bot platform / Support / Security**
- Зависит от: `00`
- Рекомендуемая модель: **GPT-5.6 Sol High**
- Рекомендуемые skills: `$telegram-engineer`, `$solution-architect`, `$backend-engineer`, `$python-engineer`, `$data-engineer`, `$security-engineer`, `$privacy-engineer`, `$platform-engineer`, `$observability-engineer`, `$qa-engineer`, `$code-reviewer`
- Основная роль: **`implementer`**
- Контракт роли: `.agents/roles/implementer.md`

## Зафиксированное решение

Использовать только:

```text
@your_fitness_coach_bot
TELEGRAM_BOT_TOKEN
```

Отдельный `support-bot`, `SUPPORT_BOT_TOKEN` и постоянный второй polling process в целевой архитектуре не нужны.

## Цель

Встроить помощь и человеческую обратную связь в основной bot lifecycle, сохранив существующие product/auth/notification contracts.

## 1. Product boundaries

Поддержка предназначена для:

- сообщения об ошибке;
- проблем со входом, аккаунтом и Telegram linking;
- вопроса о включении режима тренера или работе с клиентом;
- предложения улучшения;
- связи с владельцем/разработчиком;
- другого нестандартного вопроса.

Это не trainer-client messenger, CRM, круглосуточная линия, AI Coach, медицинская или экстренная помощь. Не обещать SLA и статус «оператор онлайн».

## 2. One runtime migration

Предпочтительно вынести router/FSM в отдельный модуль, не раздувая `bot.py`.

После миграции:

- один process владеет polling для `TELEGRAM_BOT_TOKEN`;
- linking, timezone, Mini App, notifications и feedback используют один Dispatcher lifecycle;
- сохраняется polling lock/conflict protection;
- legacy support service/config/entrypoint/env удаляются только после переноса логики и тестов;
- отдельный support token не отзывается автоматически.

Если legacy support bot уже был публичным, подготовить owner-controlled redirect:

1. короткое сообщение о переносе;
2. кнопка/deep link `@your_fitness_coach_bot?start=support`;
3. отключение старого service только после owner confirmation;
4. не принимать обращения параллельно дольше переходного периода.

## 3. Критические инварианты

Не ломать:

- `/start link_<token>`;
- linking conflict/expired token protections;
- signed TMA `initData`;
- browser Telegram login/OAuth;
- существующий login proxy-tunnel, config и TLS verification;
- timezone flow and legacy alias;
- product notification delivery/deep links;
- one internal account for Web/Telegram;
- Demo/security boundaries;
- polling lock/retry/backoff;
- запрет secrets, raw initData и private support text в логах.

Bot API polling и browser login/OAuth являются разными сетевыми сценариями. Не объединять их в неявный proxy contract.

## 4. Feedback flow

Команды `/support` и alias `/feedback` открывают категории:

```text
Ошибка
Вход или аккаунт
Предложение
Связаться с разработчиком
Другое
```

Поддержать canonical start payloads:

```text
support
support_bug
support_account
support_idea
support_contact
```

Flow:

- понятный prompt;
- privacy warning не отправлять пароли, коды, токены, платёжные данные и лишние документы;
- text/photo/document и только явно поддержанные media через safe copy/forward без обязательной загрузки файла;
- unsupported media получает понятный ответ;
- `/cancel`, TTL/reset and restart-safe state policy;
- свободный текст вне активного feedback flow не пересылается автоматически.

## 5. Owner/admin relay

- разрешённые admin ids из existing secure config;
- обращение содержит минимально нужный контекст и reply controls;
- ответ администратора отправляется нужному пользователю с ясной идентичностью;
- admin reply нельзя подменить обычным user message;
- blocked/deleted chat handled without endless retry;
- no cross-user mix-up;
- rate limits and abuse controls per user/category/window;
- audit events без текста обращения и чувствительных данных.

## 6. Compatibility with main notifications

Bot backlog не зависит формально от main task numbering. После main task `64`, если она выполнена позже, запускается narrow regression:

- one bot process;
- notification jobs still deliver;
- feedback router order не перехватывает notification callbacks;
- config/env merge не возвращает второй token/service.

## Проверки

Start/link priority, support deep links, FSM reset/expiry, unsupported media, admin permissions, reply routing, blocked user, rate limit, no secrets/log leakage, one polling owner, proxy-tunnel/auth regression and notification compatibility.

## Done when

Один публичный бот безопасно обрабатывает product entry и human feedback без превращения в generic messenger.

## Процесс

Не переходить к task `02` автоматически.
