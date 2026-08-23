# Политика применения новых skills к выполненным задачам

## Решение

Tasks `00-55` не выполняются повторно. Их task-файлы находятся в `tasks/done/` и остаются историческим evidence того, как scope был закрыт. Новые roles/skills сами по себе не являются основанием переигрывать функциональность.

## Mobile/TMA-first without rerunning completed tasks

Task `49B1` закрыла доказанные visual/component/mobile consistency gaps completed production UI без изменения feature scope. Task `50A` создала continuous mobile/TMA gate и не повторяла завершённый feature work. Невизуальные или более глубокие completed-scope проблемы остаются входом task `76`, если они не являются текущим release blocker.

## Почему одного финального audit недостаточно

Финальный gate проверяет интегрированный релиз, но он слишком поздний и широкий для глубокого предметного review каждой формулы, accessibility pattern или privacy boundary. Поэтому перед usability testing остаётся task `76` - отдельный ретроспективный audit фактического кода актуальными skills. Она не должна повторять уже закрытый `49B1` product-wide UI consistency pass без нового evidence.

## Что разрешено task 76

- проверить текущий результат, tests, migrations и docs;
- закрыть подтверждённые P0/P1;
- выполнить небольшой безопасный P2;
- вынести крупный P2 владельцу;
- зафиксировать области, где исправления не нужны.

## Что запрещено

- переигрывать исторические tasks;
- переписывать архитектуру без finding;
- запускать третий redesign;
- добавлять post-release функции;
- заявлять проблему только потому, что старый task не называл новый skill.

task `79` использует результаты task `76`, реальных сессий task `77` и operational evidence task `78` как последние входы для go/no-go.
