# TASK 02. Понятные команды, главное меню и оформление BotFather

- Фаза: **Bot UX / BotFather**
- Зависит от: `01`
- Рекомендуемая модель: **GPT-5.6 Sol High**
- Рекомендуемые skills: `$telegram-engineer`, `$product-discovery`, `$product-designer`, `$accessibility-engineer`, `$technical-writer`, `$qa-engineer`
- Основная роль: **`implementer`**
- Контракт роли: `.agents/roles/implementer.md`

## Commands in private chat

```text
start - Главное меню
app - Открыть приложение
support - Помощь и обратная связь
settings - Настройки и уведомления
help - Возможности и команды
privacy - Политика конфиденциальности
```

Aliases: `/feedback`, `/cancel`, existing `/timezone` where required. No `/news` before the post-release channel workstream.

## `/start` priority

1. `link_<token>`;
2. support payloads;
3. existing canonical app payloads;
4. unknown -> main menu without raw error.

Generic handler must never intercept linking.

## Main menu

```text
[Открыть приложение]
[Помощь и обратная связь]
[Настройки]
[Что умеет бот]
```

## Requirements

- one command source in code;
- idempotent `setMyCommands`;
- private-chat scope;
- `/app` uses current HTTPS Mini App URL;
- `/settings` uses canonical product notification preferences where available;
- `/privacy` points to real policy;
- metadata sync failure does not restart forever;
- prepare exact BotFather owner checklist, but do not execute owner-only changes.

## Accessibility и понятность

- labels кнопок понятны без иконок и не обрезаются на типичном mobile viewport;
- команды и callback confirmations используют обычный русский без внутренних терминов;
- критические действия не различаются только emoji/цветом;
- после ошибки есть понятный следующий шаг;
- inline keyboard order предсказуем;
- BotFather description не обещает функций вне release scope.

## Checks

Fresh/existing linked/unlinked user, link payload, support payload, unknown command, TMA button, mobile labels, no news command.

## Done when

Bot purpose and actions are clear without command guessing.

## Процесс

Не переходить к task `03`.
