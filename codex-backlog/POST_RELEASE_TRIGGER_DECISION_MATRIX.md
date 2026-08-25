# Trigger and owner decision matrix

Перед запуском направления заполнить его строку фактическим evidence. Для downstream task
дополнительно проверить dependency и собственный checkpoint из task-файла.

| Task/direction | Evidence source | Baseline | Observed problem/demand | Decision rule | Owner decision | Date |
|---:|---|---|---|---|---|---|
| `80` | | | | | | |
| `81` | | | | | | |
| `82` | | | | | | |
| `83A` | | | | | | |
| `84` | | | | | | |
| `88` | | | | | | |
| `89A` | Real owner preview task `88` и feedback в текущей сессии | Task `89` владеет images/moderation/publication | Служебный plain-text draft не является готовым канальным постом; exact preview/publish parity не зафиксирована | После завершения `89` нужен отдельный formatted artifact gate перед `90` | `Go`: создать `89A`, выполнить только после `89` | 2026-08-26 |
| `91` direction gate -> запуск `91A` | | | | | | |
| `92` direction gate -> запуск `92A` | | | | | | |
| `93` | | | | | | |
| `94` | | | | | | |
| `95` | | | | | | |
| `96` | | | | | | |
| `87C1` memory | | | | | | |
| `87C2` provider routing | | | | | | |

Допустимые решения: `Go`, `Defer`, `No-Go`, `Research first`. Пустая строка, product rank или
завершённая dependency не считаются согласием.
