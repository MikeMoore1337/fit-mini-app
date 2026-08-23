# Role routing guide v2 - task-declared

## Источник маршрута

Для backlog task маршрут задаёт сама task:

- `Основная роль` - единственная роль, которую нужно загрузить в начале;
- `Дополнительные роли lifecycle` - точный набор следующих ролей;
- отсутствие роли в этих полях означает, что её не нужно добавлять "для надёжности".

Role отвечает за ответственность агента, skill - за профильный рабочий контракт, task - за scope и результат. Не создавай роль или агента на каждый skill.

## Нормальные маршруты

| Ситуация | Маршрут |
|---|---|
| Локальная feature/UI task | `implementer`, затем только явно указанный `independent-reviewer` |
| Feature с существенным behavior/data risk | `implementer -> independent-reviewer -> qa-verifier`, только если обе роли указаны task |
| Discovery/design brief | профильная primary role без автоматического reviewer/QA |
| Dedicated review gate | `independent-reviewer` как primary; не добавлять ещё один independent review |
| Audit/release | `orchestrator`/`integration-release` с последовательными risk streams из task |

## Researcher

Подключай `researcher` только когда task явно его требует либо есть отдельная неизвестность, которую выгодно закрыть read-only: неизвестный contract, architecture boundary, data/auth state или внешний platform behavior. Обычное чтение файлов implementer'ом не требует researcher.

## Independent review

Reviewer проверяет текущую task и diff, а не весь продукт. Первый pass - единственный полный review. Findings образуют закрытый набор.

- `BLOCKER/HIGH` - блокируют и возвращаются primary writer на fix.
- `MEDIUM/LOW/NIT/OUT_OF_SCOPE` - не блокируют и не создают новый workstream.
- Каждый `MEDIUM/LOW` перед финализацией синхронизируется primary agent в корневом
  `NON_BLOCKING_FINDINGS.md`; reviewer/QA передают registry-ready данные, не меняя production code.
- после blocking fix reviewer выполняет только targeted recheck этих findings и регрессий от fix.

Обычная task имеет максимум 2 review passes: full + targeted. Не запускать новый full review после каждого исправления.

## QA

`qa-verifier` запускается только если task его явно перечисляет или он primary. Один pass покрывает минимальную risk matrix; после blocking fix повторяется только failed/affected scenario.

## Когда следующий task уже является gate

Не дублируй дорогой review в implementation task, если следующий task предназначен именно для этого gate и текущая task не требует review. Примеры текущего backlog:

- `49B -> 49C` - owner comparison/review gate;
- `49E -> 49F` - final owner approval gate;
- `78 -> 79` - final integrated audit/go-no-go.

## Параллельная запись

Несколько write-agents допустимы только при явно независимых streams, отдельных worktrees/ветках и заданной точке интеграции. В обычной single-task сессии должен быть один production writer.
