---
name: technical-writer
description: >
  Create or maintain long-term project documentation for setup, architecture, APIs, operations,
  deployment, migrations and contributor workflows. Use when a change makes project documentation
  inaccurate or when durable operational/architectural context is needed; follow repository
  language rules.
---

# technical-writer

Документация должна позволить другому инженеру выполнить действие без устного контекста.

По необходимости документируй:

- prerequisites;
- local setup;
- environment variables без секретных значений;
- run/test/lint/build commands;
- migrations;
- architecture overview;
- API contracts;
- integration setup;
- deployment;
- troubleshooting;
- operational runbooks;
- limitations.

Проверяй команды по реальному репозиторию, не выдумывай их.

Не дублируй документацию библиотеки или очевидный код.

Если поведение изменилось - обнови документацию в той же задаче.


## Структура документации

Сначала изучи существующую структуру документации и следуй ей. Не создавай новую иерархию
каталогов без необходимости. Если долговременная техническая документация ещё не организована,
предложи минимальную структуру по назначению (например architecture, features, operations), но
не навязывай её простому локальному изменению.

Перед изменением существующей подсистемы проверь связанную с ней документацию. Документируй
значимые архитектурные решения, неочевидные бизнес-правила, security constraints, operational
procedures и существенные trade-offs.

## Язык и аудитория

Следуй языку документации, закреплённому в root `AGENTS.md`/project rules. Не смешивай языки без
причины; названия API, библиотек, команд и identifiers оставляй в их исходном виде.

Пиши документацию для конкретного действия/решения, а не как пересказ кода.

## Audit material

Treat detailed audit output as internal by default. Generated/raw audit reports should go to the repository's configured artifact/scratch location
and should not be committed by default. Keep a durable audit document in project documentation
only when the task explicitly requires a persistent audit record. Never expose internal audit
material through a public application or published user documentation.
