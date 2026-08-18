# TASK 83. AI app knowledge - бесплатный grounded retrieval

- Фаза: **AI grounding**
- Приоритет: **83/93**
- Зависит от: `50`
- Рекомендуемый reasoning: **Medium/High**

## Цель

Научить AI Coach достоверно отвечать о фактическом Your Fitness Coach без платных embeddings/vector DB
и без выдумывания экранов/кнопок.

## In scope

Проверить текущие `docs/`, README и фактическую реализацию Web/Telegram. При необходимости создать
минимальную пользовательскую knowledge base в `docs/ai-knowledge/` с разделами overview/web/telegram,
workouts/programs/nutrition/progress/faq - только если это оправдано текущей документацией.

Выбрать минимальный бесплатный retrieval:
- существующий поиск;
- PostgreSQL FTS;
- структурированный Markdown search;
- небольшой локальный индекс.

Реализовать `search_app_help` как read-only tool, возвращающий только релевантные фрагменты.
Нет подтверждённого ответа -> AI явно признаёт недостаток достоверной информации.

Knowledge text считать недоверенными данными с точки зрения prompt injection.

## Out of scope

Не копировать весь исходный код в knowledge base. Не подключать платные embeddings, внешнюю vector DB,
тяжёлую RAG-инфраструктуру или web search.

## Проверки

Unit tests: relevant retrieval, no result, platform-specific Web/Telegram help, hallucination fallback,
injected instructions inside knowledge ignored, bounded fragment sizes.

## Done when

`search_app_help` grounding работает локально/бесплатно, а ответы об интерфейсе основываются на
актуальной документации и фактическом продукте.

## Рекомендуемый commit

`feat(ai): add grounded app knowledge retrieval`

## Процесс и отчёт

Следовать `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`. Не переходить к следующему task.
После изменений запускать только профильные проверки согласно `AGENTS.md`, проверить diff и создать один
логический commit, если task меняет tracked files. В финальном отчёте перечислить:
изменения, ключевые файлы, миграции, реально запущенные проверки, ограничения и commit hash.

## Public knowledge-base boundary
Разделить `app_help` и reviewed `fitness_knowledge` task `50`. Не копировать статьи в отдельный AI corpus без необходимости. Current AI может использовать reviewed fitness knowledge только в пределах policy; никакого trainer-client data expansion.
