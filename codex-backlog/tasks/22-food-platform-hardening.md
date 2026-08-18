# TASK 22. Food/Progress backend hardening и документация

- Фаза: **Core hardening**
- Приоритет: **22/93**
- Зависит от: `15`, `16`, `17`, `18`, `19`, `20`, `21`
- Рекомендуемый reasoning: **High**

## Цель

Стабилизировать Food + Progress backend перед массовым UI и заморозить его как источник истины для дальнейшего редизайна и AI tools.

## In scope

Проверить вместе:
- migrations/backfill safety;
- API contracts/status/error shape;
- ownership/RBAC/privacy;
- timezone/day boundaries;
- PostgreSQL indexes по реальным queries (`user_id+date`, barcode, normalized search/source ids, trainer relation где нужно);
- N+1/pagination;
- provider timeout/fallback/cache policy;
- env examples/defaults;
- observability без приватного content;
- docs food domain, provenance/license/import/search/timezone/adherence.

Проверить critical backend flow: create/find food -> add diary -> aggregate day -> progress/adherence -> trainer allowed view. Никаких новых продуктовых функций.

## Out of scope

Не делать UI, не запускать unrelated full-suite без основания, не вводить Redis/search server/microservices ради hardening.



## Проверки

Targeted backend/API/security tests затронутых food/progress paths; migration smoke; query-count/performance checks там, где они обоснованы; lint/typecheck согласно проекту.

## Done when

Food/Progress backend можно считать стабильным контрактом для задач 11-27, нет известных P0/P1 privacy/ownership/timezone проблем.

## Рекомендуемый commit

`fix(food): harden nutrition and progress platform`

## Процесс и отчёт

Следовать `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`. Не переходить к следующему task. После изменений запустить только профильные проверки, проверить diff и создать один логический commit. В финальном отчёте перечислить изменения, ключевые файлы, миграции, реально запущенные проверки, ограничения и commit hash.
