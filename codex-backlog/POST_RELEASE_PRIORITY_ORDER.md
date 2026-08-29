# Порядок направлений после release gate `79`

Tasks `80-101` и их буквенные подзадачи образуют trigger-gated post-release pool. Номер task
задаёт предпочтительную последовательность реализации, но не отменяет фактический Trigger,
dependency и отдельное решение владельца.

## Последовательность pending-задач

| Task | Направление | Почему здесь |
|---:|---|---|
| `80` | Repository hygiene/security/README | Уменьшает риск утечек, мусора и stale setup до новых изменений |
| `81` | Hydration в Nutrition | Частый optional daily flow на готовых diary/report foundations |
| `82` | Daily sleep + mood | Добавляет субъективный контекст в дневные и периодические отчёты |
| `83` | Handoff отчёта trainer | Закрывает core coaching loop без публичной ссылки |
| `84` | Reminder templates | Переиспользует task `64` и данные hydration после `81` |
| `85` | Knowledge package | Низкий runtime risk, практичная польза и grounding для AI |
| `86` | PWA | Улучшает возврат к тренировке при подтверждённом Web retention gap |
| `87-91` | AI Coach beta и period insights | Сначала privacy/provider gate, затем grounded core, tools, evals, rollout и bounded report insights |
| `92A-92B` | Advanced AI | Memory и multiprovider остаются рядом с AI Coach, но запускаются независимо только после evidence beta |
| `93` | AI-assisted import XLSX/CSV/TXT/DOCX | После AI-кластера объединяет форматы в один безопасный pipeline и создаёт программу только после предпросмотра и подтверждения |
| `94A-94B` | Распознавание еды по фото | Важная функция после основного AI Coach-кластера: feasibility/eval, затем только подтверждаемый draft |
| `95A-95B` | Server PDF и внешняя доставка | Нужны только при доказанном gap после in-product handoff `83` |
| `96` | Wearables discovery | Research-only для конкретного data/platform job |
| `97` | Delegated admins | Требует реальной команды и responsibility matrix |
| `98` | Native feasibility | Только при измеримом ограничении Web/TMA/PWA |
| `99A-99C` | Billing/монетизация | По решению владельца оставлено почти в самом конце |
| `100A-100B` | Английская локализация | По решению владельца оставлена в хвосте |
| `101` | Приватные фотографии прогресса | Последняя очередь; AI/body analysis полностью исключён |

## Почему импорт объединён и поставлен после AI

Прежние tasks `81-program-import-xlsx-csv` и `95-program-import-txt-docx` объединены в task `93`.
Пользовательский job один и тот же: загрузить существующую программу, проверить распознанную
структуру и получить редактируемый draft. Формат файла меняет детерминированный extractor, но не
должен создавать второй продуктовый pipeline.

AI предлагает нейтральную структуру программы и помогает ранжировать только ограниченный список
кандидатов упражнений. Поиск кандидатов, пороги, права доступа, валидация и запись остаются
детерминированными. Неоднозначное упражнение всегда требует ручного выбора; AI-score сам по себе
не разрешает автоматическое сопоставление или создание canonical exercise.

## Routing rules

- Umbrella `90`, `92`, `94`, `95`, `99`, `100` — coordination contracts, а не executable tasks.
- Внутри обязательных цепочек соблюдать порядок: `87 -> 88 -> 89 -> 90A -> 90B -> 91`,
  `94A -> 94B`, `95A -> 95B`, `99A -> 99B -> 99C`, `100A -> 100B`.
- `92A` и `92B` независимы: потребность в memory не доказывает потребность во втором provider.
- Task `93` запускается после решений AI-кластера `87-92`; optional `92A/92B` могут завершиться
  `Defer/No-Go` и не блокируют импорт.
- Food-photo выполняется после основного AI-блока: сначала task `94A`, а task `94B` — только после
  owner `Go/Narrow Go` с зафиксированными thresholds, privacy и cost contract.
- `83` не заменяет `95B`: первая task создаёт authenticated in-product handoff текущему trainer,
  вторая отдельно владеет expiring share/Telegram delivery.
- `101` не включает и не порождает AI-анализ фото тела, оценку формы или рекомендации по внешности.
- После любой task остановиться; следующая задача требует отдельного запуска.

Завершённые Telegram-задачи `103-106` архивированы и не входят в pending-последовательность.
Owner-selected task `106` завершила discoverability Telegram Mini App, поддержки и публичного
канала на Landing и не изменила порядок `80-101`.

Owner-selected task `107` создана вне pending-последовательности для scheduled regression и
закрытых Allure-отчётов. Её owner-approved scope не меняет current task `81` или порядок `81-101`;
implementation и внешние DNS/Cloudflare/hosting actions требуют отдельного запуска/approval.

Owner-selected task `108` создана вне pending-последовательности для product-wide аудита
соответствия законодательству РФ и непрерывного legal-impact gate будущих задач. Она не меняет
current task `81` или порядок `81-101`; запуск, legal review и любые remediation/external actions
требуют отдельных owner decisions.

Owner-selected tasks `109-111` также находятся вне pending-последовательности: factual Landing
offer, private avatar upload и Progress bento dashboard. Они не меняют current task `81` или
порядок `81-101`, не образуют общую implementation batch и запускаются только отдельными owner
решениями.

Owner-selected task `112` завершена и архивирована вне pending-последовательности после локального
review/QA zero-downtime deployment contract. Отдельно разрешённый production rollout revision
`194cf036` завершён через `single-slot` fallback с bounded downtime и verdict `active`; production
blue/green zero observed downtime на constrained VPS не заявляется. Current task `81` и порядок
`81-101` не изменились.
