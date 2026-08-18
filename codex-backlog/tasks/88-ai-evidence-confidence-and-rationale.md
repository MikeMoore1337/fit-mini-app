# TASK 88. AI Coach: evidence, confidence и «Почему?»

- Фаза: **AI Coach**
- Приоритет: **88/93**
- Зависит от: `32`, `56`, `58`, `85`, `86`, `87`
- Рекомендуемая модель: **GPT-5.6 Sol High**

## Цель

Сделать значимые рекомендации Coach объяснимыми и confidence-aware.

## In scope

- Structured evidence bundle: fact/metric, period, source tool, sufficiency, limitation.
- Strong recommendation requires sufficient data; limited => qualified language.
- API/UI support `Почему?` with factual bullets.
- Do not expose chain-of-thought; only product rationale/evidence.
- No fake confidence percentages.
- Test sparse/contradictory/stale-memory cases.

## Out of scope

Без chain-of-thought, confidence=92%, красивого сокрытия недостатка данных.

## Проверки

Sufficient/limited/insufficient, contradictions, stale memory, tool failure, no CoT leakage.

## Done when

Coach объясняет рекомендации фактами и честно признаёт недостаток данных.

## Рекомендуемый commit

`feat(ai): add evidence-aware recommendations`

## Процесс

Следовать корневому `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`.

Все предыдущие tasks считаются выполненными. Текущий код, Git history и актуальный `docs/` — source of truth.
Не проводить повторный полный аудит репозитория, не перечитывать все task-файлы и весь `masters/`.
Если текущий task относится к одному master — читать только его. Использовать результаты предыдущих audit вместо повторного исследования.
Исследовать только релевантные файлы и подсистемы. Если функция уже существует — переиспользовать, не дублировать.
Крупное изменение вне scope не начинать автоматически: зафиксировать follow-up.

Работать только в текущей feature-ветке. Не create/switch branch, merge/rebase, deploy и не переходить к следующему task.
После реализации: только профильные checks, `git diff`, один логический commit при tracked changes, краткий отчёт с reused/changed/files/migrations-config/checks/follow-ups/hash.

## Final release integration: progression rationale

Если Coach говорит о следующей нагрузке,
его evidence должно ссылаться на deterministic progression result task `58`,
а не на скрытый LLM расчёт.

## User-facing evidence language

Do not render raw internal statuses such as:
`RIR coverage insufficient; adherence 0.83`.

Prefer:
`За последние две недели выполнено 5 из 6 тренировок.
Повторы в запасе отмечены только в 3 рабочих подходах, поэтому оценка интенсивности пока ограничена.`
