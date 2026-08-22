# TASK 00. Аудит текущего Telegram runtime и архитектурный контракт

- Фаза: **Audit / Bot platform**
- Рекомендуемая модель: **GPT-5.6 Sol High**
- Рекомендуемые skills: `$telegram-engineer`, `$solution-architect`, `$security-engineer`, `$privacy-engineer`, `$platform-engineer`, `$observability-engineer`, `$technical-writer`
- Основная роль: **`researcher`**
- Контракт роли: `.agents/roles/researcher.md`

## Цель

Точечно проверить текущий Telegram-код и зафиксировать безопасную архитектуру одного публичного бота до любых изменений.

## Обязательные источники

- root `AGENTS.md`;
- текущий bot runtime, config, compose/deploy и tests;
- `REFERENCE_FORMER_MAIN_TASK_59A.md`;
- текущий результат notification orchestration, если main task уже выполнена;
- Git history и актуальный `docs/`.

## Проверить

- основной runtime `bot/fitminiapp_bot/bot.py` или фактический эквивалент;
- legacy `support_bot.py`, `support_config.py`, отдельный compose service и support env contract;
- `/start link_<token>`, account linking conflicts/expiry;
- signed TMA `initData` auth;
- browser Telegram login/OAuth proxy-tunnel и TLS verification;
- timezone commands/settings;
- notification delivery/deep links;
- polling lock/conflict protection/retry;
- текущие commands/BotFather/menu button;
- существующие feedback handlers, admin ids and privacy/logging;

## Output

Составить компактную карту:

```text
Уже есть | Переиспользовать | Перенести | Удалить после миграции | Не трогать
```

Зафиксировать stable boundaries so this backlog can be executed before or after the main notification task. Если main notification orchestration выполняется позже, оставить explicit narrow compatibility check, а не блокировать bot backlog.

## Ограничения

Не менять код, токены, BotFather, production compose или канал. Не проводить полный аудит репозитория.

## Done when

Есть проверенный план одного bot runtime и список инвариантов/рисков без предположений.

## Процесс

Не переходить к task `01` автоматически.
