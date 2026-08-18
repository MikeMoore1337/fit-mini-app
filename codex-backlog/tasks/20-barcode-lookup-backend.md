# TASK 20. Barcode lookup backend и fallback flow

- Фаза: **Core integration**
- Приоритет: **20/93**
- Зависит от: `17`, `19`
- Рекомендуемый reasoning: **Medium**

## Цель

Подготовить надёжный серверный barcode lookup до добавления camera scanning в UI.

## In scope

Barcode lookup priority: local DB -> enabled external provider -> structured `not found`, позволяющий UI предложить manual user food creation. Валидировать формат/длину в разумных пределах без выдуманного универсального стандарта.

Не дублировать provider logic. Сохранять provenance. Не раскрывать upstream errors. Ручной ввод штрихкода должен поддерживаться API независимо от камеры.

## Out of scope

Не реализовывать camera access/Barcode Detection API/client library - это task 42. Не делать платный barcode API.



## Проверки

Local hit, external hit, provider disabled, provider failure, not-found, invalid input, ownership/source metadata.

## Done when

Есть стабильный barcode lookup contract, на который позже можно безопасно посадить camera/manual UX.

## Рекомендуемый commit

`feat(food): add barcode lookup flow`

## Процесс и отчёт

Следовать `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`. Не переходить к следующему task. После изменений запустить только профильные проверки, проверить diff и создать один логический commit. В финальном отчёте перечислить изменения, ключевые файлы, миграции, реально запущенные проверки, ограничения и commit hash.
