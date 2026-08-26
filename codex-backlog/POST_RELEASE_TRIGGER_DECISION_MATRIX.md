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
| `90` | Явное подтверждение владельца в текущей сессии; опубликованные snapshots цепочки `88` → `89` → `89A` | Канал регулярно получает прошедшие owner moderation материалы; recurring private digest по умолчанию отсутствует | Владелец подтвердил пользовательский интерес к недельной подборке и отдельно одобрил consent copy/version `weekly-news-v1` | Запускать только с default-off opt-in, отдельным approval exact digest revision и мгновенной изолированной отпиской | `Go`: Trigger подтверждён, текст согласия одобрен | 2026-08-26 |
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
