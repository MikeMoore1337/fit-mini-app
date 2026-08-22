# Telegram Core backlog v5.1 changelog

## Причина пересборки

После подготовки v5 владелец уточнил, что Telegram tasks `00` и `01` уже выполнены. Поэтому они не должны получать новые версии или исполняться повторно.

## Изменения

- удалены task-файлы `00` и `01` из поставляемого пакета;
- `00/01` зафиксированы как completed immutable prerequisites;
- следующая task изменена на `02`;
- task `02` явно начинает работу от текущего repository state после `01`;
- запрещён повторный аудит/реализация `00/01`;
- сохранена максимальная автоматизация Bot API profile/public UX;
- task `03` остаётся заблокирована до main `64`;
- task `04` остаётся финальным Telegram gate после main `72`;
- owner manual actions сведены к истинным BotFather/production boundaries.
