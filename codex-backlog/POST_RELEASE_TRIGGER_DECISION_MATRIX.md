# Trigger and owner decision matrix

Перед запуском направления заполнить его строку фактическим evidence. Для downstream task
дополнительно проверить dependency и собственный checkpoint из task-файла.

| Task/direction | Evidence source | Baseline | Observed problem/demand | Decision rule | Owner decision | Date |
|---:|---|---|---|---|---|---|
| `80` | | | | Release `79` закрыт; owner запускает bounded cleanup без history rewrite | | |
| `81` | | | | Реальные XLSX/CSV подтверждают повторяемую экономию ручного переноса | | |
| `82` | | | | Есть повторяемый optional hydration job и подтверждён report/reminder scope | | |
| `83` | | | | Daily subjective context полезен пользователю/тренеру и не дублирует weekly check-in | | |
| `84` | | | | Есть потребность в explicit handoff сверх пассивного coach access | | |
| `85` | | | | Пользователи явно включают meal/water/movement templates; anti-spam contract принят | | |
| `86` | | | | Есть editorial capacity, primary sources и подтверждённые вопросы пользователей | | |
| `87` | | | | Измеримый Web return/installability gap не закрывается текущим shell | | |
| `88` | | | | Определены конкретные AI jobs, privacy boundary, evals и допустимая стоимость | | |
| `89` | Результат `88` | | | Только explicit owner `Go` после provider/privacy decision | | |
| `90` | Результат `89` | | | Grounded core прошёл evals; доказана потребность в consented personal tools | | |
| `91A` | Результат `90` | | | Core/tools готовы к internal UI/evaluation gate | | |
| `91B` | Результат `91A` | | | Есть реальные participants, consent и готовность к ограниченному rollout | | |
| `92` | | | | `91B` завершилась rollout Go, а пользователи просят interpretation factual report | | |
| `93A` memory | | | | `91B` доказала конкретный repeated continuity job | | |
| `93B` provider routing | | | | `91B` выявила измеримый provider outage/capability/cost gap | | |
| `94A` | | | | После AI-блока manual food entry friction измерим; owner одобрил bounded research/provider-cost boundary | | |
| `94B` | Результат `94A` | | | Только owner `Go/Narrow Go` с locked cases/thresholds/privacy/cost | | |
| `95` | | | | Pipeline `81` доказал ценность, но значимая доля реальных программ приходит в TXT/DOCX | | |
| `96A` | | | | Browser print-to-PDF из `67` не закрывает повторяемый delivery job | | |
| `96B` | Результат `96A` | | | Отдельно доказан temporary share и/или Telegram delivery | | |
| `97` | | | | Подтверждён один конкретный wearable datum/platform/job | | |
| `98` | | | | Есть реальная команда и owner-approved responsibility matrix | | |
| `99` | | | | Есть измеримое ограничение Web/TMA/PWA, требующее native feasibility | | |
| `100A` | | | | Есть payer/value contract и измеримые operating/AI/storage costs | | |
| `100B` | Результат `100A` | | | Только explicit commercial/provider `Go` | | |
| `100C` | Результат `100B` | | | Sandbox стабилен; owner утвердил цены, тексты и rollout cohort | | |
| `101A` | | | | Подтверждены target segment, reviewer capacity и scope первой волны | | |
| `101B` | Результат `101A` | | | Locale foundation стабильна; подтверждены public/SEO/content scope и reviewer | | |
| `102` | | | | Есть повторяющийся спрос и готов sensitive-media lifecycle; AI/body analysis исключён | | |

## Завершённые owner decisions

| Task/direction | Evidence source | Baseline | Observed problem/demand | Decision rule | Owner decision | Date |
|---:|---|---|---|---|---|---|
| `103` | Owner-selected editorial flow | | | Stable Telegram Core и owner moderation capacity | `Go`, выполнено | 2026-08-26 |
| `104` | Результат `103` | | | Требовались images/moderation/publication boundaries | `Go`, выполнено | 2026-08-26 |
| `104A` | Real owner preview task `103` и feedback | Task `104` владеет images/moderation/publication | Служебный plain-text draft не является готовым канальным постом | После `104` нужен formatted artifact gate перед `105` | `Go`, выполнено | 2026-08-26 |
| `105` | Опубликованные snapshots цепочки `103 -> 104 -> 104A` | Recurring private digest по умолчанию отсутствовал | Подтверждён интерес к недельной подборке и consent copy/version `weekly-news-v1` | Только default-off opt-in и мгновенная изолированная отписка | `Go`, выполнено | 2026-08-26 |

Допустимые решения для pending: `Go`, `Defer`, `No-Go`, `Research first`. Пустая строка, номер или
завершённая dependency не считаются согласием.
