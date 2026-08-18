# TASK 90. AI Coach UI - общий Web + Telegram Mini App интерфейс

- Фаза: **AI product UI**
- Приоритет: **90/93**
- Зависит от: `05`, `38`, `87`, `88`, `89`
- Рекомендуемый reasoning: **Medium**
- Рекомендуемые skills: $product-designer`, `$frontend-engineer`, при необходимости `$qa-engineer

## Цель

Встроить рабочий AI Coach в общий frontend так, чтобы Web и Telegram Mini App использовали одну
продуктовую логику и backend, без отдельного AI-приложения.

## In scope

Использовать существующие design system/app shell. Минимальный экран:
- название и короткое описание;
- история сообщений;
- input/send;
- loading/error/retry/empty;
- стартовые подсказки;
- controlled unavailable state;
- различимый случай, когда общий chat доступен, но персональный tool-анализ временно недоступен из-за
отсутствия бесплатного tool-capable provider.

Стартовые запросы покрывают Today, Progress, exercise load, замену упражнения, КБЖУ, app help.
Не показывать raw tool calls/JSON/provider names/errors, если это не является осознанным пользовательским UX.

Безопасный Markdown/text rendering, без unsafe `innerHTML`. Не утверждать, что write request выполнен.
Streaming не использовать.

Web и Telegram Mini App переиспользуют общий UI/state/API слой. На этом task нужна функциональная
Telegram совместимость; финальный platform-specific polish всего продукта остаётся task 72.

## Out of scope

Не создавать отдельный Telegram frontend, provider-specific UI, streaming, write controls, voice/image/video
AI или новый app shell.

## Проверки

Component/e2e: empty/history/send/loading/retry, general/personal/app-help/out-of-scope, write request,
all providers unavailable, no tool-capable provider, reload/persistence, safe script/HTML rendering,
responsive 390/360 + desktop smoke, Telegram adapter compatibility.

## Done when

AI Coach функционально работает в Web и Telegram Mini App через общий frontend/backend, ошибки и
ограничения понятны пользователю, а provider/tool internals скрыты.

## Рекомендуемый commit

`feat(ai): add shared ai coach experience`

## Процесс и отчёт

Следовать `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`. Не переходить к следующему task.
После изменений запускать только профильные проверки согласно `AGENTS.md`, проверить diff и создать один
логический commit, если task меняет tracked files. В финальном отчёте перечислить:
изменения, ключевые файлы, миграции, реально запущенные проверки, ограничения и commit hash.

## Backlog v3 personalized Coach UX
UI: `Что Coach помнит обо мне?`, delete/clear memory, `Почему?`, insufficient-data states, nutrition/training prompts, shared Web/TMA conversations. Do not present AI as autonomous trainer.

## Final release integration: no autonomous engagement spam

AI Coach не создаёт reminders/notifications сам.
Если в будущем появятся AI-triggered reminders, это отдельный post-release feature.

## Beginner-friendly Coach UI

Quick prompts, tooltips, empty states and suggestions use natural Russian.

Do not make `RIR`, `TDEE`, `adherence`, `deload`, `primary exposure`
the only visible wording.

Where useful:
`понятное название (профессиональный термин)`.
