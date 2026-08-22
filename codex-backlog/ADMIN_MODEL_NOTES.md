# Account capabilities и Admin model - release v6

## Модель

```text
Authenticated Account
├── Personal capabilities
├── Trainer capability - user-enabled
└── Root Admin - server-configured
```

## Personal

Каждый authenticated account сохраняет личные тренировки, программы, питание, цели КБЖУ, замеры и Progress независимо от дополнительных capabilities.

## Trainer

- Trainer mode включается пользователем напрямую в Profile/Settings.
- Нет заявки, beta gate, очереди модерации, approve/reject, документов или статуса «проверенный тренер».
- Перед включением показывается краткое объяснение возможностей и ответственности.
- Trainer additive: личный режим остаётся доступен, client workspace открывается отдельно.
- Не создавать связь тренера с самим собой.
- Trainer не получает Admin автоматически.
- Отключение режима не удаляет клиентские данные и не нарушает историю; активные связи обрабатываются предсказуемо и явно.
- Доступ к клиенту существует только при действующей связи и разрешённом scope.

## Root Admin

- Root Admin определяется только server-side конфигурацией владельца/break-glass account.
- Root нельзя назначить, передать, удалить или создать через UI, API или изменение обычной роли в БД.
- Root capability независима от Trainer.
- До первого релиза нет delegated admins, support_admin, super_admin, content_admin и интерфейса управления администраторами.
- Frontend controls не являются security boundary; все операции проверяются backend.

## UI

- Profile показывает отдельные Personal, Trainer и Root/Admin entry points только при фактическом capability.
- При работе с клиентом интерфейс постоянно показывает имя клиента и способ возврата.
- Destructive/assignment actions формулируются с именем клиента.
- Нельзя использовать слово «верифицирован», «проверен» или аналогичное без реальной процедуры проверки.

## Post-release

Delegated/team roles возможны только по отдельной post-release task после появления реальной команды и доказанной потребности.
