# TASK 38. App shell и primary navigation

- Фаза: **Core UX**
- Приоритет: **38/93**
- Зависит от: `05`, `06`, `07`, `22`
- Рекомендуемый reasoning: **High**
- Рекомендуемые skills: `$product-designer`, `$frontend-engineer`

## Цель

Убрать ощущение admin-панели из равноправных tabs и создать устойчивую IA, которая уже учитывает Today/Training/Progress/Nutrition и будущий AI без второго frontend.

## In scope

Переработать AppShell, client primary navigation, desktop/mobile layout, role-specific Trainer/Admin entry, account/theme/logout presentation. Целевая mobile-модель максимум 5 destination примерно `Сегодня / План(Тренировки) / Прогресс / Питание / Ещё`, точные названия адаптировать по фактическому продукту.

Mobile Web и TMA: одна и та же mobile navigation/composition, bottom nav, icon+label, active state не только цветом, safe-area, контент не под nav, без desktop account cluster. Telegram-specific behavior не должен создавать отдельный nav design.
Desktop: отдельная композиция - compact sidebar/rail или устойчивый top nav по данным; forms readable width, data screens шире.
Back/forward/deep links сохраняются. Landmarks, `aria-current`, focus. Trainer/Admin доступны без перегрузки client nav. AI пока не обязан быть одним из пяти главных пунктов. Если AppShell показывает бренд, использовать shared canonical logo/mark из task `07`, а не локальную копию SVG. AppShell должен использовать shared YFC Light/Dark tokens из task `08`; не создавать отдельные Web/TMA visual variants.

## Out of scope

Не редизайнить содержимое разделов, не менять RBAC/backend, не делать router rewrite без необходимости, не ломать deep-link/query flows.



## Проверки

Playwright 1440/1280/768/390/360: destinations, back/forward, roles, theme/logout, overflow, safe-area; на 390/360 проверить visual/layout parity Mobile Web и TMA в рамках shared YFC UI. Связанные component/e2e/typecheck/lint/build.

## Done when

Все разделы достижимы; mobile <=5 главных destination; Mobile Web/TMA используют одну mobile composition; desktop имеет собственную responsive-композицию; nav keyboard accessible.

## Рекомендуемый commit

`feat(ui): redesign app shell and primary navigation`

## Процесс и отчёт

Следовать `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`. Не переходить к следующему task. После изменений запустить только профильные проверки, проверить diff и создать один логический commit. В финальном отчёте перечислить изменения, ключевые файлы, миграции, реально запущенные проверки, ограничения и commit hash.

## Knowledge navigation
База знаний доступна из app secondary navigation/`Ещё` и contextual links, но не обязана занимать один из <=5 primary mobile destinations. Public `/knowledge`/`/exercises` не ломают authenticated navigation.
