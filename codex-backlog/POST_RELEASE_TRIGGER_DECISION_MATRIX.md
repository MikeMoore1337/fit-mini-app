# Trigger and owner decision matrix

Перед запуском направления заполнить его строку фактическим evidence. Для downstream task
дополнительно проверить dependency и собственный checkpoint из task-файла.

| Task/direction | Evidence source | Baseline | Observed problem/demand | Decision rule | Owner decision | Date |
|---:|---|---|---|---|---|---|
| `80` | | | | Release `79` закрыт; owner запускает bounded cleanup без history rewrite | | |
| `81` | | | | Есть повторяемый optional hydration job и подтверждён report/reminder scope | | |
| `82` | | | | Daily subjective context полезен пользователю/тренеру и не дублирует weekly check-in | | |
| `83` | | | | Есть потребность в explicit handoff сверх пассивного coach access | | |
| `84` | | | | Пользователи явно включают meal/water/movement templates; anti-spam contract принят | | |
| `85` | | | | Есть editorial capacity, primary sources и подтверждённые вопросы пользователей | | |
| `86` | | | | Измеримый Web return/installability gap не закрывается текущим shell | | |
| `87` | | | | Определены конкретные AI jobs, privacy boundary, evals и допустимая стоимость | | |
| `88` | Результат `87` | | | Только explicit owner `Go` после provider/privacy decision | | |
| `89` | Результат `88` | | | Grounded core прошёл evals; доказана потребность в consented personal tools | | |
| `90A` | Результат `89` | | | Core/tools готовы к internal UI/evaluation gate | | |
| `90B` | Результат `90A` | | | Есть реальные participants, consent и готовность к ограниченному rollout | | |
| `91` | Результат `90B` | | | Rollout получил `Go`, а пользователям нужна интерпретация factual report | | |
| `92A` memory | Результат `90B` | | | Beta доказала конкретный repeated continuity job | | |
| `92B` provider routing | Результат `90B` | | | Beta выявила измеримый provider outage/capability/cost gap | | |
| `93` | Corpus XLSX/CSV/TXT/DOCX и AI decisions `87-92` | | | Файлы дают повторяемую экономию ручного переноса; extraction и exercise-matching evals проходят заданные пороги, privacy/cost contract принят | | |
| `94A` | | | | После AI-блока manual food entry friction измерим; owner одобрил bounded research/provider-cost boundary | | |
| `94B` | Результат `94A` | | | Только owner `Go/Narrow Go` с locked cases/thresholds/privacy/cost | | |
| `95A` | | | | Browser print-to-PDF из `67` не закрывает повторяемый delivery job | | |
| `95B` | Результат `95A` | | | Отдельно доказан temporary share и/или Telegram delivery | | |
| `96` | | | | Подтверждён один конкретный wearable datum/platform/job | | |
| `97` | | | | Есть реальная команда и owner-approved responsibility matrix | | |
| `98` | | | | Есть измеримое ограничение Web/TMA/PWA, требующее native feasibility | | |
| `99A` | | | | Есть payer/value contract и измеримые operating/AI/storage costs | | |
| `99B` | Результат `99A` | | | Только explicit commercial/provider `Go` | | |
| `99C` | Результат `99B` | | | Sandbox стабилен; owner утвердил цены, тексты и rollout cohort | | |
| `100A` | | | | Подтверждены target segment, reviewer capacity и scope первой волны | | |
| `100B` | Результат `100A` | | | Locale foundation стабильна; подтверждены public/SEO/content scope и reviewer | | |
| `101` | | | | Есть повторяющийся спрос и готов sensitive-media lifecycle; AI/body analysis исключён | | |
| `107` | Owner request и аудит current GitHub Actions/test harness | Большой regression scope уже существует, но нет schedule, единого Allure HTML, очевидной browser-ссылки, закрытого доступа и явного lifecycle отчётов | Владелец утвердил `allure.your-fitness-coach.ru`, Cloudflare Access allowlist, Daily `14` дней и Weekly `4` отчёта | Task creation approved; implementation требует отдельного owner запуска, а DNS/Cloudflare/hosting/secrets — дополнительного explicit approval | Создать task, implementation pending | 2026-08-28 |
| `108` | Прямой owner request на проверку соответствия законодательству РФ | Существующие security/privacy/product audits не дают полного legal-risk coverage и не охватывают автоматически ещё не созданные задачи | Владелец потребовал охватить весь проект, все backlog tasks и любые будущие задачи через continuous gate | Task creation approved; Stage A read-only audit, обязательный RF counsel review baseline/gate, Stage B, `LEGAL_COUNSEL_REQUIRED`, remediation и external legal actions имеют отдельные checkpoints | Создать task, audit pending | 2026-08-28 |

## Завершённые owner decisions

| Task/direction | Evidence source | Baseline | Observed problem/demand | Decision rule | Owner decision | Date |
|---:|---|---|---|---|---|---|
| `103` | Owner-selected editorial flow | | | Stable Telegram Core и owner moderation capacity | `Go`, выполнено | 2026-08-26 |
| `104` | Результат `103` | | | Требовались images/moderation/publication boundaries | `Go`, выполнено | 2026-08-26 |
| `104A` | Real owner preview task `103` и feedback | Task `104` владеет images/moderation/publication | Служебный plain-text draft не является готовым канальным постом | После `104` нужен formatted artifact gate перед `105` | `Go`, выполнено | 2026-08-26 |
| `105` | Опубликованные snapshots цепочки `103 -> 104 -> 104A` | Recurring private digest по умолчанию отсутствовал | Подтверждён интерес к недельной подборке и consent copy/version `weekly-news-v1` | Только default-off opt-in и мгновенная изолированная отписка | `Go`, выполнено | 2026-08-26 |
| `106` | Owner-approved Landing task и screenshot evidence | Telegram destinations были смешаны | Канонические Main Mini App/support/news links | Явные distinct links без нового runtime | `Go`, выполнено | 2026-08-28 |

Допустимые решения для pending: `Go`, `Defer`, `No-Go`, `Research first`. Пустая строка, номер или
завершённая dependency не считаются согласием.
