# TASK 84. AI read-only tools, context builder и bounded agent loop

- Фаза: **AI agent core**
- Приоритет: **84/93**
- Зависит от: `22`, `32`, `33`, `34`, `35`, `40`, `41`, `43`, `44`, `48`, `82`
- Рекомендуемый reasoning: **High**

## Цель

Подключить AI Coach к фактическим данным приложения безопасными read-only tools и реализовать ограниченный
agent loop без доверия к model-supplied identity.

## In scope

На основе аудита зарегистрировать минимальный allowlist, например:
`get_user_profile_summary`, `get_user_goal_and_targets`, `get_current_training_program`,
`get_today_workout`, `get_training_history`, `get_exercise_history`, `get_progress_summary`,
`get_nutrition_targets`, `get_heart_rate_zones`, `get_exercise_info`.
Финальные имена адаптировать к реальному проекту.

Жёстко:
- tools только read-only;
- user определяется auth/session backend, модель не задаёт доверенный `user_id`;
- ownership/RBAC проверяется при каждом tool;
- минимальный результат, без secrets/internal IDs;
- Pydantic/существующая валидация args;
- unknown tool reject;
- никакого arbitrary SQL/HTTP/code;
- лимит размера tool result;
- `AI_MAX_TOOL_ROUNDS`;
- write request только получает рекомендацию, данные не меняются.

Context builder передаёт только необходимые обезличенные данные. Детерминированные BMR/TDEE/КБЖУ,
пульсовые зоны и другие расчёты брать из существующих сервисов: LLM объясняет, но не пересчитывает.

Agent loop должен сохранять согласованный conversation/tool context при provider failover. Tool output,
как и user/knowledge text, считать данными, а не system instruction.

Если нужен tool, а router не имеет tool-capable free provider, вернуть контролируемую недоступность
персонального анализа.

## Out of scope

Не добавлять write tools, arbitrary access, автоматическое изменение программ/КБЖУ/профиля, web search,
MCP или multi-agent архитектуру.

## Проверки

Unit/API-level tests: allowlist, auth-derived identity, чужой user_id, cross-user access, invalid args,
unknown tool, write request, tool-output injection, max rounds, oversized result, deterministic calculations
from backend, failover inside agent loop, no tool-capable provider.

## Done when

AI может безопасно читать только разрешённые данные текущего пользователя, tool loop ограничен, а
существующие backend calculations остаются единственным источником истины.

## Рекомендуемый commit

`feat(ai): add readonly app tools and agent loop`

## Процесс и отчёт

Следовать `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`. Не переходить к следующему task.
После изменений запускать только профильные проверки согласно `AGENTS.md`, проверить diff и создать один
логический commit, если task меняет tracked files. В финальном отчёте перечислить:
изменения, ключевые файлы, миграции, реально запущенные проверки, ограничения и commit hash.

## Backlog v3 tool boundary
Base tools расширяются tasks `85-88`. LLM не получает generic arbitrary `user_id`; backend binds authenticated current user.
