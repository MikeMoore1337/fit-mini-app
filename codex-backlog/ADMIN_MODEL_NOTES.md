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

Trainer application:
- короткий manual access request, не professional verification;
- application history хранится отдельно от current Trainer capability;
- approve выполняется только Root/super_admin или explicit `trainer_applications.manage`;
- support_admin read-only;
- self-review запрещён;
- approve атомарно активирует Trainer capability и пишет audit event;
- документы/verified badge/marketplace не входят в первый релиз.

Текущая convenience-связь `admin => trainer` должна быть удалена без уничтожения реального trainer status.

Trainer может пользоваться AI Coach для собственных Personal данных.
AI Coach не получает данные клиентов trainer.
Trainer Copilot - отдельный будущий epic.


## Auth integration
Admin tasks now run after auth tasks `10-13`. Root remains bound to trusted Telegram identity; multi-provider linking cannot transfer Root authority.
