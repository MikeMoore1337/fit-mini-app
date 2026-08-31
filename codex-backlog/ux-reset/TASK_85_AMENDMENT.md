# Amendment to existing Task 85 - Knowledge package

**Не использовать этот файл вместо существующей Task 85. Добавить пункты в её scope/acceptance.**

## Dependency и placement

- Task 85 выполняется после Task 121 либо поверх уже интегрированного Public Web handoff Task 121.
- Task 85 остаётся вне critical path Task 124A, если владелец отдельно не включил её в текущий RC.

## Canonical Public Web contract

- Индекс материалов живёт на canonical Public Web URL `/knowledge`.
- Опубликованный материал живёт на `/knowledge/{category}/{slug}`.
- Изменение этих public paths требует redirect/canonical/sitemap review; Task 85 не создаёт второй app-only URL contract.
- Long-form article, index, sources, editorial metadata и SEO rendering принадлежат Public Web.

## App и Telegram Mini App handoff

- В authenticated app/TMA остаётся только короткая contextual help рядом с конкретным действием.
- Ссылка на long reading открывает canonical Public Web URL в новой вкладке/внешнем browser.
- В TMA обычный click использует поддерживаемый `Telegram.WebApp.openLink`; unavailable/error оставляет явный безопасный Web-link fallback.
- Knowledge Base не возвращается в primary/secondary app navigation, `Ещё`, Profile или отдельный TMA reader.
- Известные legacy `/app/knowledge...` routes получают redirect/handoff на соответствующий `/knowledge...`, а не 404.

## Exercise technique boundary

- Техника упражнения, media phases и guide dialog остаются contextual in-app flow.
- Task 85 не переносит exercise guide dialog в Public Web и не создаёт always-expanded long-form help на core screens.

## Additional acceptance

- [ ] Long-form package опубликован только на canonical Public Web paths.
- [ ] App/TMA показывают только context-specific handoff без permanent Knowledge destination.
- [ ] Web handoff использует безопасный new-tab contract; TMA использует `openLink` с fallback.
- [ ] Legacy known routes имеют redirect/handoff strategy.
- [ ] Exercise technique остаётся доступной внутри app.
