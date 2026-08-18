# TASK 82. AI domain policy - topic gate, system prompt и medical boundary

- Фаза: **AI domain core**
- Приоритет: **82/93**
- Зависит от: `81`
- Рекомендуемый reasoning: **High**

## Цель

Создать продуктовую политику AI Coach: он остаётся фитнес-ассистентом даже при prompt injection и отказах
провайдеров, а не превращается в общего чат-бота.

## In scope

Реализовать versioned system prompt отдельно от business code и topic policy:
`allowed`, `not_allowed`, `medical_boundary`, `app_help`.

Разрешённая область: фитнес, питание, спортивное питание, тренировки и использование Your Fitness Coach.
Вне scope: программирование, политика, история, право, финансы, автомобили, бытовые вопросы, развлечения,
отношения, тексты, новости и прочие темы.

Medical boundary: не диагностировать, не назначать лечение/рецептурные препараты; ААС/SARMs/лекарственные
схемы вне MVP. Допустима общая безопасная тренировочная информация и рекомендация обратиться к специалисту.

Topic gate:
- не получает tools и лишние персональные данные;
- классифицирует, а не отвечает;
- возвращает строгую структуру;
- использует бесплатный router и по возможности лёгкую модель;
- пользовательский текст рассматривает как данные;
- при полной недоступности gate использует безопасный fallback;
- не удваивать LLM calls без необходимости, если безопасная архитектура позволяет объединить классификацию
с основным запросом без ослабления policy.

Защитить system policy от `ignore previous instructions`, reveal prompt/secrets и смены роли.

## Out of scope

Не реализовывать user tools, app knowledge retrieval, persistence или UI. Не добавлять фармакологию/AAS
в разрешённую область.

## Проверки

Unit tests/policy cases: allowed fitness/nutrition/sports nutrition/app help; out-of-scope; medical boundary;
prompt injection; reveal system prompt/key; nested instructions; gate provider unavailable safe fallback.
Не использовать full-string equality для LLM output.

## Done when

Есть единый versioned policy layer, который ограничивает тему и медицинскую границу независимо от
конкретного provider и не раскрывает system instructions/secrets.

## Рекомендуемый commit

`feat(ai): add coach policy and topic gate`

## Процесс и отчёт

Следовать `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`. Не переходить к следующему task.
После изменений запускать только профильные проверки согласно `AGENTS.md`, проверить diff и создать один
логический commit, если task меняет tracked files. В финальном отчёте перечислить:
изменения, ключевые файлы, миграции, реально запущенные проверки, ограничения и commit hash.
