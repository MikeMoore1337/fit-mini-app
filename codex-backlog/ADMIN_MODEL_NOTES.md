# Admin model notes

`ADMIN_TELEGRAM_USER_IDS` остаётся Root Admin / owner / break-glass source of truth.

Root:
- server-side only;
- не создаётся/удаляется через UI;
- может управлять delegated admins;
- не получает Trainer автоматически.

Delegated admins:
- DB-managed;
- least privilege;
- не могут создать Root.

Personal - baseline.
Trainer = Personal + Trainer.
Admin = Personal + Admin.
Trainer + Admin допустимы вместе.

Текущая convenience-связь `admin => trainer` должна быть удалена без уничтожения реального trainer status.

Trainer может пользоваться AI Coach для собственных Personal данных.
AI Coach не получает данные клиентов trainer.
Trainer Copilot - отдельный будущий epic.


## Auth integration
Admin tasks now run after auth tasks `10-13`. Root remains bound to trusted Telegram identity; multi-provider linking cannot transfer Root authority.
