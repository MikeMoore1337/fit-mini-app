# Приоритет направлений после release gate `79`

Tasks `80-96` и их буквенные подзадачи находятся в общей папке `codex-backlog/tasks/`, но образуют trigger-gated pool, а не
обязательную линейную очередь. Номер сохраняет product rank исходного направления и удобство
ссылок. Он не разрешает реализацию без evidence, dependencies и owner decision.

| Product rank | Tasks | Направление | Trigger в одном предложении |
|---:|---|---|---|
| `01` | `80` | Приватные фотографии прогресса | Есть повторяющийся запрос и готово безопасное image storage |
| `02` | `81` | XLSX/CSV import | Тренеры/пользователи теряют измеримое время на ручной перенос таблиц |
| `03` | `82` | PWA | Web return/launch ограничивает удержание после фактических performance fixes |
| `04` | umbrella `83` -> `83A-83C` | Монетизация | Есть operating costs или доказанная готовность платить за конкретную ценность |
| `05-08` | `84-86`, umbrella `87` -> `87A-87B` | Ограниченная AI Coach beta | Есть конкретный AI job, прошедший safety/privacy/eval и real-user gates |
| `09-11` | `88-90` | Telegram editorial/news | Бот стабилен, owner готов модерировать, аудитория отдельно запрашивает контент/digest |
| `12` | umbrella `91` -> `91A-91B` | Английская локализация | Есть измеримый target segment и capacity на native review/support/content |
| `13` | umbrella `92` -> `92A-92B` | Серверный PDF/delivery | Browser print-to-PDF не закрывает регулярный подтверждённый delivery job |
| `14` | `93` | Wearables discovery | Конкретный ручной ввод или integration gap измеримо мешает approved job |
| `15` | `94` | Делегированные admins | Появилась реальная команда и owner-approved responsibility matrix |
| `16` | `95` | TXT/DOCX import | Pipeline `81` доказал ценность, а значимая доля программ остаётся в поддерживаемых документах |
| `17` | `96` | Native feasibility | Web/TMA/PWA ограничения измеримо вредят критическому сценарию |
| `18` | umbrella `87C` -> independently gated `87C1`, `87C2` | Advanced AI | Beta отдельно доказала спрос на memory и/или provider resilience |

Текущее routing-состояние Telegram news потока: tasks `88-90` завершены и архивированы. Следующей
current остаётся release task `74`; umbrella `91` отдельно не выполняется, а `91A` требует
собственных dependency, Trigger и owner decision.

## Routing rules

- Umbrella `83`, `87`, `87C`, `91`, `92` читать как общий contract, но не выполнять. Например,
  английская локализация выполняется `91A -> отдельная остановка/решение -> 91B`; task `91` до или
  после них не запускается.
- Task `81` может быть первым post-release implementation, а `80` — отложен: rank не заменяет Trigger.
- Внутри dependency chains порядок обязателен: `84 -> 85 -> 86 -> 87A -> 87B`,
  `88 -> 89 -> 89A -> 90`,
  `83A -> 83B -> 83C`, `91A -> 91B`, `92A -> 92B`.
- После `87B` advanced capabilities остаются independent: `87C1` и `87C2` запускаются отдельно
  только по собственному Trigger; task `87C` не запускается.
- Task `95` запускается только после доказанной ценности и стабильного pipeline `81`.
- `87C1` и `87C2` независимы: потребность в memory не доказывает потребность во втором provider, и
  наоборот.
- После любой task остановиться; следующая задача требует отдельного запуска.
