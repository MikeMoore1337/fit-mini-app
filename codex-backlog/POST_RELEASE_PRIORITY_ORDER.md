# Порядок направлений после release gate `79`

Tasks `80-102` и их буквенные подзадачи образуют trigger-gated post-release pool. Сам номер task
теперь задаёт предпочтительную последовательность реализации: отдельного product rank больше нет.
Номер не отменяет фактический Trigger, dependency и отдельное решение владельца.

## Последовательность pending-задач

| Task | Направление | Почему здесь |
|---:|---|---|
| `80` | Repository hygiene/security/README | Уменьшает риск утечек, мусора и stale setup до новых изменений |
| `81` | XLSX/CSV import | Даёт trainer workflow измеримую экономию ручного переноса |
| `82` | Hydration в Nutrition | Частый optional daily flow на готовых diary/report foundations |
| `83` | Daily sleep + mood | Добавляет субъективный контекст в дневные и периодические отчёты |
| `84` | Handoff отчёта trainer | Закрывает core coaching loop без публичной ссылки |
| `85` | Reminder templates | Переиспользует task `64` и данные hydration после `82` |
| `86` | Knowledge package | Низкий runtime risk, практичная польза и grounding для AI |
| `87` | PWA | Улучшает возврат к тренировке при подтверждённом Web retention gap |
| `88-92` | AI Coach beta и period insights | Сначала privacy/provider gate, затем grounded core, tools, evals, rollout и bounded report insights |
| `93A-93B` | Advanced AI | Memory и multiprovider остаются рядом с AI Coach, но запускаются независимо только после evidence beta |
| `94A-94B` | Распознавание еды по фото | Важная функция после всего AI Coach-кластера: feasibility/eval, затем только подтверждаемый draft |
| `95` | TXT/DOCX import | Расширяет доказавший ценность pipeline `81` |
| `96A-96B` | Server PDF и внешняя доставка | Нужны только при доказанном gap после in-product handoff `84` |
| `97` | Wearables discovery | Research-only для конкретного data/platform job |
| `98` | Delegated admins | Требует реальной команды и responsibility matrix |
| `99` | Native feasibility | Только при измеримом ограничении Web/TMA/PWA |
| `100A-100C` | Billing/монетизация | По решению владельца оставлено почти в самом конце |
| `101A-101B` | Английская локализация | По решению владельца оставлена в хвосте |
| `102` | Приватные фотографии прогресса | Последняя очередь; AI/body analysis полностью исключён |

## Routing rules

- Umbrella `91`, `93`, `94`, `96`, `100`, `101` — coordination contracts, а не executable tasks.
- Внутри обязательных цепочек соблюдать порядок: `88 -> 89 -> 90 -> 91A -> 91B -> 92`,
  `94A -> 94B`, `96A -> 96B`, `100A -> 100B -> 100C`, `101A -> 101B`.
- Food-photo выполняется после основного AI-блока: сначала task `94A`, а task `94B` — только после
  owner `Go/Narrow Go` с зафиксированными thresholds, privacy и cost contract.
- `93A` и `93B` независимы: потребность в memory не доказывает потребность во втором provider.
- `84` не заменяет `96B`: первая task создаёт authenticated in-product handoff текущему trainer,
  вторая отдельно владеет expiring share/Telegram delivery.
- `102` не включает и не порождает AI-анализ фото тела, оценку формы или рекомендации по внешности.
- После любой task остановиться; следующая задача требует отдельного запуска.

Завершённые Telegram-задачи `103-105` архивированы и не входят в pending-последовательность.
